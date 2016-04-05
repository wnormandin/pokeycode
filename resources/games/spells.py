#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeygame
from pokeygame import WorldTile, Player, Spell

# Dictionary containing lists of spells, by type
spell_dict = {
                'offensive': [FlameBolt]
                'status': [Paralyze]
                'seal': [ExplosiveSeal]
            }

class Paralyze(Spell):

    """ Apply the Paralyze status effect """

    def __init__(self,target,turns):

        assert isinstance(turns, int), 'Turn count must be integer!'
        self.target = target

        Super(Paralyze,self).__init__(
                                True,           # Immediately cast
                                Spell.status,
                                None, None,
                                turns,
                                None
                                )

class FlameBolt(Spell):

    """ Immediately cast a flame damage spell """

    def __init__(self,target,dmg_range):
        self.target = target
        Super(FlameBolt,self).__init__(
                                True,           # Immediately cast
                                Spell.offensive,
                                Spell.fire
                                None, 1,
                                dmg_range
                                )

class ExplosiveSeal(Spell):

    """ Fire-Based damage seal for doors, chests, and traps """

    def __init__(self):
        self.sp_type = Spell.seal,
        self.sp_elem = Spell.fire,

        # Trigger event in Player so that only
        # players can trigger seals
        self.sp_trigger = Player.trigger_seal,
        self.dmg_range = (5,15)
        self.counter = 1

        # Skip the Super call for this type
