from bots.botsconfig import *
from .records006030 import recorddefs

syntax = {
    'version': '00603',
    'functionalgroup': 'CH',
}

structure = [
{ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
    {ID: 'E6', MIN: 1, MAX: 150, LEVEL: [
        {ID: 'E8', MIN: 1, MAX: 1},
    ]},
    {ID: 'SE', MIN: 1, MAX: 1},
]}
]
