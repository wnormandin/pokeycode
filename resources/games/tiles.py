#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeygame
from pokeygame import WorldTile
import mobs
import items
import traps

easy_list = [
            GeneralHallway,
            ]

class GeneralHallway(WorldTile):

    """ Generic hallway tile """

    def __init__(self):
        kwargs = {
                'spawn_rate':10,
                'eligibles':{
                    'mobs':[mobs.GeneralMob],
                    'items':[items.GeneralItem],
                    'traps':[traps.GeneralTrap]
                    },
                'description':'A Generic Hall.  Period'
                }

        tile_name = 'A generic hall'
        tile_type = WorldTile.hallway

        super(GeneralHallway,self).__init__(tile_name,tile_type,**kwargs)

class GeneralWall(WorldTile):

    """ Generic, impassable wall """

    def __init__(self):
        args = {
                'traversable':False
                }
        tile_name = 'A wall'
        tile_type = WorldTile.wall

        super(GeneralWall,self).__init__(tile_name,tile_type,**kwargs)
