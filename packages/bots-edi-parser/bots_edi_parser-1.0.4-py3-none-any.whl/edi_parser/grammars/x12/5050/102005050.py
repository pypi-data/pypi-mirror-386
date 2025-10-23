from bots.botsconfig import *
from .records005050 import recorddefs

syntax = {
    'version': '00505',
    'functionalgroup': 'AC',
}

structure = [
{ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
    {ID: 'ORI', MIN: 1, MAX: 1},
    {ID: 'REF', MIN: 0, MAX: 99999},
    {ID: 'OOI', MIN: 1, MAX: 99999},
    {ID: 'BDS', MIN: 1, MAX: 1},
    {ID: 'SE', MIN: 1, MAX: 1},
]}
]
