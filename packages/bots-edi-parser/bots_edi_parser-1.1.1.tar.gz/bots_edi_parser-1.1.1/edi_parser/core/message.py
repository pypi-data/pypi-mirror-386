"""
EDI Parser message lib
Extracted from Bots
"""
# pylint: disable=missing-function-docstring

# edi_parser modules
from . import global_config as botsglobal
# from . import grammar
from . import node
from .config import (
    BOTSIDNR,
    ID,
    MPATH,
    MANDATORY,
    MAXREPEAT,
    SUBFIELDS,
    FIELDS,
    SFIELD,
    VALUE,
    MIN,
    MAX,
    ISFIELD,
    LEVEL,
)
from ..lib.utils import gettext as _
from .exceptions import MappingFormatError, MappingRootError, MessageError, MessageRootError


class Message:
    """
    abstract class; represents a edi message.
    is subclassed as outmessage or inmessage object.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, ta_info):
        self.ta_info = ta_info  # here ta_info is only filled with parameters from db-ta
        self.errorlist = []  # collect non-fatal errors in the edi file; used in reporting errors.
        self.errorfatal = True  # store fatal errors: errors that stop the processing of the file
        self.messagetypetxt = ''  # used in reporting errors.
        self.messagecount = 0  # count messages in edi file; used in reporting errors.
        self.root = None  # Add lwx 20190917
        self.defmessage = None
        self.syntax = {}

    def add2errorlist(self, errortxt):
        """Handle non-fatal parse errors"""
        # In validate_only mode, collect all errors without limits
        validate_only = self.ta_info.get('validate_only', False)

        if not validate_only:
            # Check if field_validation_mode is 'strict' - raise exception instead of logging
            validation_mode = self.ta_info.get('field_validation_mode', 'lenient')
            if validation_mode == 'strict' and ('[F' in errortxt or '[E' in errortxt):
                # For field validation errors in strict mode, raise exception
                from .exceptions import MessageError
                raise MessageError(self.messagetypetxt + errortxt)

        # UNITTEST_CORRECTION
        # raise MessageError("For unit format test")
        # if more than max_number_errors: stop adding new errors to list.
        # In validate_only mode, collect ALL errors (no limit)
        max_errors = float('inf') if validate_only else botsglobal.ini.getint('settings', 'max_number_errors', 10)

        if len(self.errorlist) < max_errors:
            self.errorlist.append(self.messagetypetxt + errortxt)
        elif len(self.errorlist) == max_errors:
            self.errorlist.append(
                (
                    _('Found at least %(max_number_errors)s errors.')
                    % {'max_number_errors': len(self.errorlist)}
                )
            )

    def checkforerrorlist(self):
        """examine the message-object for errors"""
        if self.errorfatal:  # for fatal errors: (try to) get information like partners for edi file
            self.try_to_retrieve_info()

        # In validate_only mode, don't raise exceptions - just collect errors
        validate_only = self.ta_info.get('validate_only', False)
        if self.errorlist and not validate_only:
            raise MessageError("".join(self.errorlist))

    def try_to_retrieve_info(self):
        """
        when edi-file is not correct, (try to) get info about eg partnerID's in message
        method is specified in subclasses.
        """

    @staticmethod
    def display(lex_records):
        """for debugging: display lexed records."""
        # pylint: disable=consider-using-f-string
        for lex_record in lex_records:
            counter = 0
            for veld in lex_record:
                if counter == 0:
                    print('%s    (Record-id)' % (veld[VALUE]))
                else:
                    if veld[SFIELD] == 0:
                        print('    %s    (field)' % (veld[VALUE]))
                    elif veld[SFIELD] == 1:
                        print('        %s    (sub)' % (veld[VALUE]))
                    elif veld[SFIELD] == 2:
                        print('        %s    (rep)' % (veld[VALUE]))
                    else:
                        print('    %s    (???)' % (veld[VALUE]))
                counter += 1

    @staticmethod
    def mpathformat(mpath):
        """mpath is eg: ['UNH', 'NAD'], formatted is: 'UNH-NAD'."""
        return '-'.join(mpath)

    def checkmessage(self, node_instance, defmessage, subtranslation=False):
        """
        The node tree is check, sorted, fields are formatted etc against grammar.
        (so far only minimal tests have been done during processing)

        For checking translation & subtranslation
        parameter 'subtranslation' only used for reporting
        some different cases:
        - empy root.record, root.children filled:
        - edifact, x12, tradacoms: each child is an envelope. Check each envelope.
          (use mailbag to have one UNB per node-tree here)
        - csv nobotsid: each child is a record. Check all records in one check
        - xml, json:
        root.record filled, root.children filled: outgoing messages.
        """
        if not self.ta_info['has_structure']:
            return
        if node_instance.record:
            # root record contains information; so one message
            count = 1
            self._checkonemessage(node_instance, defmessage, subtranslation)
        else:
            count = 0
            for childnode in node_instance.children:
                count += 1
                self._checkonemessage(childnode, defmessage, subtranslation)
        if count < defmessage.structure[0][MIN]:
            self.add2errorlist(
                _(
                    '[S03] Root record "%(mpath)s" occurs %(count)d times, min is %(mincount)d.\n'
                ) % {
                    'mpath': defmessage.structure[0][ID],
                    'count': count,
                    'mincount': defmessage.structure[0][MIN]
                })
        if count > defmessage.structure[0][MAX]:
            self.add2errorlist(
                _(
                    '[S04] Root record "%(mpath)s" occurs %(count)d times, max is %(maxcount)d.\n'
                ) % {
                    'mpath': defmessage.structure[0][ID],
                    'count': count,
                    'maxcount': defmessage.structure[0][MAX]
                })

    def _checkonemessage(self, node_instance, defmessage, subtranslation):
        structure = defmessage.structure
        if node_instance.record['BOTSID'] != structure[0][ID]:
            raise MessageRootError(
                _(
                    '[G50]: Grammar "%(grammar)s" starts with record "%(grammarroot)s";'
                    ' but in edi-file found start-record "%(root)s".'
                ),
                {
                    'root': node_instance.record['BOTSID'],
                    'grammarroot': structure[0][ID],
                    'grammar': defmessage.grammarname,
                },
            )
        self._checkifrecordsingrammar(node_instance, structure[0], defmessage.grammarname)
        self._canonicaltree(node_instance, structure[0])
        # should the content of the message (the records read) be logged.
        if not subtranslation and botsglobal.ini.getboolean('settings', 'readrecorddebug', False):
            self._logmessagecontent(node_instance)

    def _checkifrecordsingrammar(self, node_instance, structure, grammarname):
        """check for every node if in grammar recursive"""
        # list of records not in the grammar; these records are deleted at end of function
        deletelist = []
        # check if fields are known in grammar
        self._checkiffieldsingrammar(node_instance, structure)
        if 'messagetype' in node_instance.queries:
            # SUBTRANSLATION starts; do not check (already checked)
            return
        if node_instance.children and LEVEL not in structure:
            # record has children, but these are not in the grammar
            if self.ta_info['checkunknownentities']:
                self.add2errorlist(
                    _(
                        '[S01]%(linpos)s: Record "%(record)s" in message has children,'
                        ' but these are not in grammar "%(grammar)s". Found record "%(xx)s".\n'
                    )
                    % {
                        'linpos': node_instance.linpos(),
                        'record': node_instance.record['BOTSID'],
                        'grammar': grammarname,
                        'xx': node_instance.children[0].record['BOTSID'],
                    }
                )
            node_instance.children = []
            return
        for childnode in node_instance.children:
            # for every record/childnode:
            for record_definition in structure[LEVEL]:
                # search in grammar-records
                if childnode.record['BOTSID'] == record_definition[ID]:
                    # found record in grammar
                    # check recursive:
                    self._checkifrecordsingrammar(childnode, record_definition, grammarname)
                    # record/childnode is in gramar;
                    # go to check next record/childnode
                    break
            else:
                # record/childnode is not in grammar
                if self.ta_info['checkunknownentities']:
                    self.add2errorlist(
                        _('[S02]%(linpos)s: Unknown record "%(record)s" in message.\n')
                        % {'linpos': node_instance.linpos(), 'record': childnode.record['BOTSID']}
                    )
                deletelist.append(childnode)
        for child in deletelist:
            node_instance.children.remove(child)

    def _checkiffieldsingrammar(self, node_instance, record_definition):
        """
        checks for every field in record if field exists in record_definition (from grammar).
        for inmessage of type (var,fixed,??) this is not needed
        """
        # pylint: disable=too-many-branches, too-many-nested-blocks
        # check every field in the record
        for field in list(node_instance.record.keys()):
            if field == 'BOTSIDnr':
                # BOTSIDnr is not in grammar, so skip check
                continue
            for field_definition in record_definition[FIELDS]:
                if field_definition[ISFIELD]:
                    # field (no composite)
                    if field == field_definition[ID]:
                        # OK!
                        break
                else:
                    # if composite
                    if field_definition[MAXREPEAT] == 1:
                        # non-repeating composite
                        # loop subfields
                        for grammarsubfield in field_definition[SUBFIELDS]:
                            if field == grammarsubfield[ID]:
                                # break out of grammarsubfield-for-loop
                                # ->goto break out of field_definition-for-loop
                                break
                        else:
                            # nothing found; continue with next gammarfield
                            continue
                        # break out of field_definition-for-loop
                        break
                    # repeating composite
                    if field == field_definition[ID]:
                        # OK. Contents is a list of dicts;
                        # TODO: check for each dict if sub-fields exist in grammar.
                        break
            else:
                # field not found in grammar
                if self.ta_info['checkunknownentities']:
                    self.add2errorlist(
                        _('[F01]%(linpos)s: Record: "%(mpath)s" has unknown field "%(field)s".\n')
                        % {
                            'linpos': node_instance.linpos(),
                            'field': field,
                            'mpath': self.mpathformat(record_definition[MPATH]),
                        }
                    )
                del node_instance.record[field]

    def _formatfield(self, value, field_definition, structure_record, node_instance):
        """
        Format of a field is checked and converted if needed.
        Input: value (string), field definition.
        Output: the formatted value (string)
        Parameters of self.ta_info are used: triad, decimaal
        for fixed field: same handling; length is not checked.
        """
        # pylint: disable=unused-argument
        return value

    def _canonicaltree(self, node_instance, structure):
        """
        For nodes: check min and max occurence;
        sort the records conform grammar
        """
        sortednodelist = []
        # handle fields of this record
        self._canonicalfields(node_instance, structure)
        if node_instance.structure is None:
            node_instance.structure = structure
        if LEVEL in structure:
            # for every record_definition (in grammar) of this level
            for record_definition in structure[LEVEL]:
                # count number of occurences of record
                count = 0
                # for every node in mpathtree; SPEED: delete nodes from list when found
                for childnode in node_instance.children:
                    # if it is not the right NODE":
                    if childnode.record['BOTSID'] != record_definition[ID] \
                            or childnode.record['BOTSIDnr'] != record_definition[BOTSIDNR]:
                        continue
                    count += 1
                    # use rest of index in deeper level
                    self._canonicaltree(childnode, record_definition)
                    sortednodelist.append(childnode)
                if record_definition[MIN] > count:
                    self.add2errorlist(
                        _(
                            '[S03]%(linpos)s: Record "%(mpath)s" occurs %(count)d times,'
                            ' min is %(mincount)d.\n'
                        )
                        % {
                            'linpos': node_instance.linpos(),
                            'mpath': self.mpathformat(record_definition[MPATH]),
                            'count': count,
                            'mincount': record_definition[MIN],
                        }
                    )
                if record_definition[MAX] < count:
                    self.add2errorlist(
                        _(
                            '[S04]%(linpos)s: Record "%(mpath)s" occurs %(count)d times,'
                            ' max is %(maxcount)d.\n'
                        )
                        % {
                            'linpos': node_instance.linpos(),
                            'mpath': self.mpathformat(record_definition[MPATH]),
                            'count': count,
                            'maxcount': record_definition[MAX],
                        }
                    )
            node_instance.children = sortednodelist

    def _canonicalfields(self, node_instance, record_definition):
        """
        For all fields: check M/C, format.
        Fields are not sorted (a dict can not be sorted).
        Fields are never added.
        """
        # pylint: disable=too-many-branches, too-many-nested-blocks, too-many-statements
        noderecord = node_instance.record
        # loop over fields in grammar
        for field_definition in record_definition[FIELDS]:
            if field_definition[ISFIELD]:
                # field (no composite)
                if field_definition[MAXREPEAT] == 1:
                    # non-repeating
                    value = noderecord.get(field_definition[ID])
                    if not value:
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F02]%(linpos)s: Record "%(mpath)s" field "%(field)s"'
                                    ' is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )
                        continue
                    noderecord[field_definition[ID]] = self._formatfield(
                        value, field_definition, record_definition, node_instance
                    )
                else:
                    # repeating field;
                    # a list of values; values can be empty or None;
                    # at least one field should have value, else dropped
                    valuelist = noderecord.get(field_definition[ID])
                    if valuelist is None:
                        # empty lists are already catched in node.put()
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F41]%(linpos)s: Record "%(mpath)s" repeating field'
                                    ' "%(field)s" is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )
                        continue
                    if not isinstance(valuelist, list):
                        raise MappingFormatError(
                            _('Repeating field: must be a list: put(%(mpath)s)'),
                            {'mpath': valuelist},
                        )
                    if len(valuelist) > field_definition[MAXREPEAT]:
                        self.add2errorlist(
                            _(
                                '[F42]%(linpos)s: Record "%(mpath)s" repeating field "%(field)s"'
                                ' occurs %(occurs)s times, max is %(max)s.\n'
                            )
                            % {
                                'linpos': node_instance.linpos(),
                                'mpath': self.mpathformat(record_definition[MPATH]),
                                'field': field_definition[ID],
                                'occurs': len(valuelist),
                                'max': field_definition[MAXREPEAT],
                            }
                        )
                    newlist = []
                    repeating_field_has_data = False
                    for value in valuelist:
                        if value is None:
                            value = ''
                        else:
                            value = str(value).strip()
                            if value:
                                repeating_field_has_data = True
                        newlist.append(
                            self._formatfield(
                                value, field_definition, record_definition, node_instance
                            )
                        )
                    if not repeating_field_has_data:
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F43]%(linpos)s: Record "%(mpath)s" repeating field'
                                    ' "%(field)s" is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )
                        del noderecord[field_definition[ID]]
                        continue
                    noderecord[field_definition[ID]] = newlist
            else:
                # composite
                if field_definition[MAXREPEAT] == 1:
                    # non-repeating compostie
                    # first check if there is any data att all in this composite
                    for grammarsubfield in field_definition[SUBFIELDS]:
                        if noderecord.get(grammarsubfield[ID]):
                            # composite has data.
                            break
                    else:
                        # composite has no data
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F03]%(linpos)s: Record "%(mpath)s" composite "%(field)s"'
                                    ' is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )
                        # there is no data in composite, so do nothing
                        continue
                    # there is data in the composite!
                    # loop subfields
                    for grammarsubfield in field_definition[SUBFIELDS]:
                        value = noderecord.get(grammarsubfield[ID])
                        if not value:
                            if grammarsubfield[MANDATORY]:
                                self.add2errorlist(
                                    _(
                                        '[F04]%(linpos)s: Record "%(mpath)s" subfield "%(field)s"'
                                        ' is mandatory.\n'
                                    )
                                    % {
                                        'linpos': node_instance.linpos(),
                                        'mpath': self.mpathformat(record_definition[MPATH]),
                                        'field': grammarsubfield[ID],
                                    }
                                )
                            continue
                        noderecord[grammarsubfield[ID]] = self._formatfield(
                            value, grammarsubfield, record_definition, node_instance
                        )
                else:  # if repeating composite: list of dicts
                    valuelist = noderecord.get(field_definition[ID])
                    # empty lists are catched in node.put()
                    if valuelist is None:
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F44]%(linpos)s: Record "%(mpath)s" repeating composite'
                                    ' "%(field)s" is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )
                        continue
                    if not isinstance(valuelist, list):
                        raise MappingFormatError(
                            _('Repeating composite: must be a list: put(%(mpath)s)'),
                            {'mpath': valuelist},
                        )
                    if len(valuelist) > field_definition[MAXREPEAT]:
                        self.add2errorlist(
                            _(
                                '[F45]%(linpos)s: Record "%(mpath)s" repeating composite'
                                ' "%(field)s" occurs %(occurs)s times, max is %(max)s.\n'
                            )
                            % {
                                'linpos': node_instance.linpos(),
                                'mpath': self.mpathformat(record_definition[MPATH]),
                                'field': field_definition[ID],
                                'occurs': len(valuelist),
                                'max': field_definition[MAXREPEAT],
                            }
                        )
                    # is a list of composites; each composite is a dict.
                    # loop over composites/dicts, create a new list
                    # - dict can be empty: {}. check if: composite contains data or is empty
                    # - if composite is not-empty, check M/C of elements in composite
                    # - keys should be str.
                    # - convert values to unicode
                    # - check if there is data for whole repeating composite
                    newlist = []
                    repeating_composite_has_data = False
                    for comp in valuelist:
                        if not isinstance(comp, dict):
                            raise MappingFormatError(
                                _(
                                    'Repeating composite: each composite must be a dict:'
                                    ' put(%(mpath)s)'
                                ),
                                {'mpath': valuelist},
                            )
                        # check each dict, convert values to unicode
                        # also: check if dict has data at all
                        composite_has_data = False
                        for key, value in comp.items():
                            if not isinstance(key, str):
                                raise MappingFormatError(
                                    _('Repeating composite: keys must be strings: put(%(mpath)s)'),
                                    {'mpath': valuelist},
                                )
                            if value is None:
                                comp[key] = ''
                            else:
                                # leading and trailing spaces are stripped from the values
                                comp[key] = str(value).strip()
                                if comp[key]:
                                    composite_has_data = True
                        if composite_has_data:
                            repeating_composite_has_data = True
                            # loop subfields
                            for grammarsubfield in field_definition[SUBFIELDS]:
                                value = comp.get(grammarsubfield[ID])
                                if not value:
                                    if grammarsubfield[MANDATORY]:
                                        self.add2errorlist(
                                            _(
                                                '[F46]%(linpos)s: Record "%(mpath)s" subfield'
                                                ' "%(field)s" in repeating composite'
                                                ' is mandatory.\n'
                                            )
                                            % {
                                                'linpos': node_instance.linpos(),
                                                'mpath': self.mpathformat(record_definition[MPATH]),
                                                'field': grammarsubfield[ID],
                                            }
                                        )
                                    continue
                                comp[grammarsubfield[ID]] = self._formatfield(
                                    value, grammarsubfield, record_definition, node_instance
                                )
                        else:
                            comp = {}
                        newlist.append(comp)
                    if not repeating_composite_has_data:
                        if field_definition[MANDATORY]:
                            self.add2errorlist(
                                _(
                                    '[F47]%(linpos)s: Record "%(mpath)s" repeating composite'
                                    ' "%(field)s" is mandatory.\n'
                                )
                                % {
                                    'linpos': node_instance.linpos(),
                                    'mpath': self.mpathformat(record_definition[MPATH]),
                                    'field': field_definition[ID],
                                }
                            )

                        del noderecord[field_definition[ID]]
                    else:
                        noderecord[field_definition[ID]] = newlist

    def _logmessagecontent(self, node_instance):
        botsglobal.logger.debug('Record "%(BOTSID)s":', node_instance.record)
        # handle fields of this record
        self._logfieldcontent(node_instance.record)
        for child in node_instance.children:
            self._logmessagecontent(child)

    @staticmethod
    def _logfieldcontent(noderecord):
        for key, value in noderecord.items():
            if key not in ['BOTSID', 'BOTSIDnr']:
                botsglobal.logger.debug('    "%(key)s" : "%(value)s"', {'key': key, 'value': value})

    # ***************************************************************************
    # * methods below pass call to node.Node ************************************
    # ***************************************************************************
    def getrecord(self, *mpaths):
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'getrecord(%(mpath)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.getrecord(*mpaths)

    def change(self, where, change):
        """
        query tree (self.root) with where;
        if found replace with change;

        :return: True if change, False if not changed.
        """
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'change(%(where)s,%(change)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'where': where, 'change': change},
            )
        return self.root.change(where, change)

    def delete(self, *mpaths):
        """
        query tree (self.root) with mpath;delete if found.

        :return: True if deleted, False if not deleted.
        """
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'delete(%(mpath)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.delete(*mpaths)

    def get(self, *mpaths):
        """query tree (self.root) with mpath; get value (string); get None if not found."""
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'get(%(mpath)s): "root" of incoming message is empty; either split messages'
                    ' or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.get(*mpaths)

    def getnozero(self, *mpaths):
        """like get, returns None is value is zero (0) or not numeric.
            Is sometimes usefull in mapping."""
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'getnozero(%(mpath)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.getnozero(*mpaths)

    def getdecimal(self, *mpaths):
        """like get, returns None is value is zero (0) or not numeric.
            Is sometimes usefull in mapping."""
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'getdecimal(%(mpath)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.getdecimal(*mpaths)

    def getcount(self):
        """count number of nodes in self.root. Number of nodes is number of records."""
        return self.root.getcount()

    def getcountoccurrences(self, *mpaths):
        """count number of nodes in self.root. Number of nodes is number of records."""
        return len(list(self.getloop(*mpaths)))

    def getcountsum(self, *mpaths):
        """return the sum for all values found in mpath.
        Eg total number of ordered quantities."""
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'get(%(mpath)s): "root" of incoming message is empty;'
                    ' either split messages or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        return self.root.getcountsum(*mpaths)

    def getloop(self, *mpaths):
        """
        query tree with mpath; generates all the nodes.
        Is typically used as: for record in inn.get(mpath):
        """
        if self.root.record:
            # self.root is a real root
            # search recursive for rest of mpaths
            yield from self.root.getloop(*mpaths)
        else:
            # self.root is dummy root
            for childnode in self.root.children:
                # search recursive for rest of mpaths
                yield from childnode.getloop(*mpaths)

    def getloop_including_mpath(self, *mpaths):
        """
        as getloop, but returns a list: [mpath,mpath,etc,,node]
        ->node is same as returned by getloop()
        """
        if self.root.record:
            # self.root is a real root
            # search recursive for rest of mpaths
            yield from self.root.getloop_including_mpath(*mpaths)
        else:
            # self.root is dummy root
            for childnode in self.root.children:
                # search recursive for rest of mpaths
                yield from childnode.getloop_including_mpath(*mpaths)

    def put(self, *mpaths, **kwargs):
        if self.root.record is None and self.root.children:
            raise MappingRootError(
                _('put(%(mpath)s): "root" of outgoing message is empty; use out.putloop'),
                {'mpath': mpaths},
            )
        return self.root.put(*mpaths, **kwargs)

    def putloop(self, *mpaths):
        if not self.root.record:
            # no input yet, and start with a putloop(): dummy root
            if len(mpaths) == 1:
                self.root.append(node.Node(record=mpaths[0]))
                return self.root.children[-1]
            raise MappingRootError(
                _('putloop(%(mpath)s): mpath too long???'), {'mpath': mpaths}
            )
        return self.root.putloop(*mpaths)

    def sort(self, *mpaths):
        if self.root.record is None:
            raise MappingRootError(
                _(
                    'get(%(mpath)s): "root" of message is empty; either split messages'
                    ' or use inn.getloop'
                ),
                {'mpath': mpaths},
            )
        self.root.sort(*mpaths)
