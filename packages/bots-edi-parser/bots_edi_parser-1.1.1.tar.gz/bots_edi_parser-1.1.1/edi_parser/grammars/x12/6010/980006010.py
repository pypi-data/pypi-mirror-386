from bots.botsconfig import *
from .records006010 import recorddefs

syntax = {
    'version': '00601',
    'functionalgroup': 'IR',
}

structure = [
{ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
    {ID: 'BT1', MIN: 1, MAX: 10},
    {ID: 'SE', MIN: 1, MAX: 1},
]}
]
