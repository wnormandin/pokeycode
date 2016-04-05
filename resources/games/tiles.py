#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeygame

from pokeygame import wt as wt

easy_list = [
            Hallway,
            Wall,
            Door,
            Dungeon,
            Shop,
            BossRoom
            ]

class Dungeon(wt):

    """ Generic dungeon room tiles """

    def __init__(self):
        spwn = 0.25
        desc = "A dungeon room"
        tile_name = "Dungeon"
        tile_type = wt.dungeon

        super(Dungeon,self).__init__(
                                tile_name,
                                tile_type,
                                spawn_rate=spwn,
                                description=desc
                                )

class BossRoom(wt):

    """ Designates the room where the boss will spawn, lowest level """

    def __init__(self):
        spwn = 0
        desc = "Room with a big boss in it"
        tile_name = "Boss Room"
        tile_type = wt.boss

        super(BossRoom,self).__init__(
                                    tile_name,
                                    tile_type,
                                    spawn_rate=spwn,
                                    description=desc
                                    )

class Door(wt):

    """ Generic Door Tile """

    def __init__(self):
        spwn = 0
        desc = 'A door'
        tile_name = "A doorway"
        tile_type = wt.door

        super(Door,self).__init__(
                                tile_name,
                                tile_type,
                                spawn_rate=spwn,
                                description=desc
                                )

    def toggle_locked(self,opt=None):
        if opt is not None:
            if self.locked != opt:
                self.locked = opt
        else:
            self.locked = not self.locked

class MagicDoor(Door):

    """ Doorway sealed by magic """

    def __init__(self,spell=None):
        self.toggle_locked(True)
        self.seal_door(spell)
        super(MagicDoor,self).__init__()

    def seal_door(self,spell=None):
        if spell is not None:
            self.seal=spell
        else:
            self.seal=random_seal()
class LockedDoor(Door):

    """ Doorway to a locked room """

    def __init__(self):
       self.toggle_locked(True)
       super(LockedDoor,self).__init__()

class Hallway(wt):

    """ Generic Hallway Tile """

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
        tile_type = wt.hallway

        super(Hallway,self).__init__(tile_name,tile_type,**kwargs)

class Wall(wt):

    """ Generic, impassable wall """

    def __init__(self):
        args = {
                'traversable':False
                }
        tile_name = 'A wall'
        tile_type = wt.wall

        super(Wall,self).__init__(tile_name,tile_type,**kwargs)
