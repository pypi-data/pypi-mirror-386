from bots.botsconfig import *
from .records005030 import recorddefs

syntax = {
    'version': '00503',
    'functionalgroup': 'SO',
}

structure = [
{ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
    {ID: 'M10', MIN: 0, MAX: 1},
    {ID: 'P4', MIN: 0, MAX: 1},
    {ID: 'M15', MIN: 1, MAX: 9999, LEVEL: [
        {ID: 'V1', MIN: 0, MAX: 1},
        {ID: 'V2', MIN: 0, MAX: 1},
        {ID: 'K1', MIN: 0, MAX: 4},
    ]},
    {ID: 'SE', MIN: 1, MAX: 1},
]}
]
