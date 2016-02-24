#/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import random
import pokeygame
from pokeygame import Skill

class CombatSkill(Skill):
    """ Combat skills, botched roll temporarily reduces defense """
    
    def __init__(self,player):
        self.skill_type = Skill.combat_type
        self.level = max(player.level/5,1)
        

class StealthSkill(Skill):
    """ Stealth skills, botched roll temporarily reduces attack """
    
    def __init__(self,player):
        self.skill_type = Skill.stealth_type
        self.level = max(player.level/5,1)

class MagicSkill(Skill):
    """ Magic skills, botched roll temporarily reduces focus """
    
    def __init__(self,player):
        self.skill_type = Skill.magic_type
        self.level = max(player.level/5,1)

class MapSkill(Skill):
    """ Map and navigation skills, no botched effects """
    
    def __init__(self,player):
        self.skill_type = Skill.general_skill
        self.level = 1
