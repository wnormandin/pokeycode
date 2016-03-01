#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import math
import random
import sys
import pokeygame
from pokeygame import WorldTile

class WorldGenerator(object):

    """ Generates worlds based on the config parameters """

    def __init__(
                self,           # The World Generator object
                dim_x=10,       # x dimension range
                dim_y=10,       # y dimension range
                dim_z=2,        # z dimension range
                flex_limit=0,   # Maximum dimension fluctuation
                ):
        """ WorldGenerator creates a world_generation_template """

        self.boss_level = dim_z     # Boss on lowest level
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z
        self.min_dist = ((self.dim_x+self.dim_y)/2)/2 #1/2 the avg
        self.grid = self.erect_walls()

        #print self
        #k = raw_input("press_any_key")

        self.set_entry_point()
        self.set_descent_point()
        self.set_exit_point()
        self.build_paths()
        self.build_rooms()
        self.test_paths()

    def __str__(self):
        retval = ''
        for z in range(0,self.dim_z+1):
            retval+='\tFloor -{0}-\n'.format(z)
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    retval+= ' {0} '.format(self.grid[x,y,z])
                retval+='\n'

        return retval

    def erect_walls(self):
        grid = {}
        for z in range(0,self.dim_z+1):
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    grid[x,y,z]=WorldTile.wall

        return grid

    def set_entry_point(self):
        """ Sets the initial entry point on the map edge """

        z = 0   # Entry point is on first floor
        valid_x = (0,self.dim_x-1) # valid values (OR w/valid_y)
        valid_y = (0,self.dim_y-1)

        while True:
            x_test = random.randint(0,self.dim_x)
            y_test = random.randint(0,self.dim_y)

            if x_test in valid_x and y_test not in valid_y:
                condition = True
            elif y_test in valid_y and x_test not in valid_x:
                condition = True
            else:
                condition = False

            if condition:
                self.grid[x_test,y_test,z]=WorldTile.entry_point
                self.start = (x_test,y_test,z)
                print 'Entry point set : {0}'.format((x_test,y_test,z))
                break

    def set_descent_point(self):
        """ Sets point to descend/ascend on each level """

        i = 0
        while i < self.dim_z: # Loop until bottom floor
            x_test = random.randint(0,self.dim_x-1)
            y_test = random.randint(0,self.dim_y-1)

            if i==0:
                tile_type = WorldTile.entry_point
            else:
                tile_type = WorldTile.ascent_point

            check_point = self.find_tile(i,tile_type)

            assert check_point, 'Tile Not Found! lvl {0}:{1}\n{2}'.format(
                                                            i,
                                                            tile_type,
                                                            self
                                                            )

            if self.calc_dist(check_point,(x_test,y_test))>=self.min_dist:
                # If the distance is acceptable, set the points
                # and move to next level :

                # Add a descent point in the grid template
                self.grid[x_test,y_test,i]=WorldTile.descent_point
                print 'Descent Point Set {0}'.format((x_test,y_test,i))

                # Add corresponding ascent point on the next floor
                self.grid[x_test,y_test,i+1]=WorldTile.ascent_point
                print 'Ascent Point Set {0}'.format((x_test,y_test,i+1))
                i += 1

    def path_avail_dirs(self,pos,impediments,random=False):
        # Processes available directions, returns a random direction
        # if the random flag is passed, else returns the direction
        # list

        # impediments will contain impassable vals
        north = True if self.grid(pos[0]+1) not in impediments else False
        south = True if self.grid(pos[0]-1) not in impediments else False
        east = True if self.grid(pos[1]+1) not in impediments else False
        west = True if self.grid(pos[1]-1) not in impediments else False

        dirs = [north,south,east,west]
        assert any(dirs),'Pathing : No available moves!'

        if not random:
            return dirs
        else:
            # Randomly selects an available move and returns it
            while True:
                roll = random.randint(0,3)
                dirs = [north,south,east,west]
                if dirs[roll]:
                    retval = dirs[roll].__name__
                    break
            return retval

    def calc_dist(self,pt1,pt2):
        x_term = pt1[0]-pt2[0]
        y_term = pt1[1]-pt2[1]
        return math.sqrt(x_term**2+y_term**2)

    def find_tile(self,z,tile_type):
        """ Looks for the given tile type on the requested floor """
        retval = False
        for y in range(self.dim_y):
            for x in range(self.dim_x):
                if self.grid[x,y,z]==tile_type:
                    retval = (x,y,z)
        return retval

    def set_exit_point(self):
        """ Sets exit point on the map edge, far enough from entry """

        valid_x = (0,self.dim_x)
        valid_y = (0,self.dim_y)
        max_attempts = 500
        this_attempt = 0

        while True:
            x_test = random.randint(0,self.dim_x-1)
            y_test = random.randint(0,self.dim_y-1)
            if x_test in valid_x and y_test not in valid_y:
                condition = True
            elif y_test in valid_y and x_test not in valid_x:
                condition = True
            else:
                condition = False

            if condition:
                asc = self.find_tile(self.dim_z-1,WorldTile.ascent_point)

                assert asc,'Ascent point not found! {0}\n{1}'.format(
                                                            self.dim_z,
                                                            self)

                test = (x_test,y_test,self.dim_z)
                if self.calc_dist(asc,test)>=self.min_dist:
                    self.grid[test]=WorldTile.exit_point
                    self.end = test
                    print 'Exit Point Set {0}'.format(tuple(test))
                    return True
                    break

            this_attempt += 1

            if this_attempt >= max_attempts:
                again = raw_input('Max attempts reached, continue(y)?')
                if again not in ['y','Y']:
                    return False
                    break
                else:
                    this_attempt = 0

    def build_paths(self):
        """ Builds paths of hallways to waypoints """

        waypoints_per_floor = ((self.dim_x+self.dim_y)/2)/2
        way_list = self.build_waypoints(waypoints_per_floor)

        for i in range(len(way_list)-1):
            way1 = way_list[i]
            way2 = way_list[i+1]

            # If the two waypoints are on the same floor,
            # connect them
            if way1[2]==way2[2]:
                self.connect(way1,way2)

    def connect(self,pt1,pt2,direct=False):
        """ Connects the two points with hallway tiles """
        dist = [None,None]
        # The 0 index will signify x
        dist[0] = pt1[0]-pt2[0]
        # 1 signifies y
        dist[1] = pt1[1]-pt2[1]

        # Calculate the distance between the points (for max leg length)
        pt_dist = int(math.sqrt(dist[0]**2+dist[1]**2))
        this_leg = pt_dist

        # Set direction based on axis with maximum remaining distance
        direction = 0 if dist[0] > dist[1] else 1
        # Determine whether direction of motion is positive or negative
        positive = True if pt1[direction] < pt2[direction] else False

        # Set the opposing dir (absolute value of 1-1=0, 0-1=1)
        not_direction = abs(direction-1)

        leg_set = False     # Flag to catch when a feature is added

        tile_list = []  # List of tiles to be set
        coord_list = list(pt1)  # create a mutable coord list

        # Add a straight leg (or connect the points if in range)
        if not leg_set:

            # If pt2 is a straight shot, connect directly
            if dist[direction]==pt_dist:
                for n in range(pt_dist):    # the distance moved along the 
                    self.tile_append(
                                positive,
                                tile_list,
                                coord_list,
                                direction
                                )


            # Else the leg will bend to connect 
            else:
                while this_leg > 0:
                    if coord_list[direction]==pt2[direction]:
                        cond = coord_list[not_direction]<pt2[not_direction]
                        self.tile_append(
                                    cond,
                                    tile_list,
                                    coord_list,
                                    not_direction
                                    )
                    else:

                        self.tile_append(
                                    positive,
                                    tile_list,
                                    coord_list,
                                    direction
                                    )
                    this_leg -= 1
            for tile in tile_list:
                self.grid[tile]=WorldTile.hallway

    def tile_append(self,condition,tile_list,coord_list,index):
        #  Takes [condition] and adds a point to the list in that dir
        #  index denotes the axis (0 = x, 1 = y)
        if condition:
            offset = 1
        else:
            offset = -1
        coord_list[index]+=offset

        tile_list.append(       # axis of motion=distance to pt2
                  (coord_list[0],coord_list[1],coord_list[2])
                  )

    def build_waypoints(self,w):
        retval = []
        for z in range(self.dim_z+1):
            # Set starting waypoint for the floor
            if z == 0:
                retval.append(self.start)
            else:
                retval.append(self.find_tile(z,WorldTile.ascent_point))

            # Fill other waypoints
            for way in range(w):
                x = random.randint(0,self.dim_x)
                y = random.randint(0,self.dim_y)
                retval.append((x,y,z))

            # Set ending waypoint for the floor
            if z == self.dim_z-1:
                retval.append(self.end)
            else:
                retval.append(self.find_tile(z,WorldTile.descent_point))
        return retval

    def find_path_ends(self,z):
        """ Returns the endpoints for the given floor """
        if z == 0:
            start = self.find_tile(z,WorldTile.entry_point)
            end = self.find_tile(z,WorldTile.descent_point)
        elif z == self.dim_z:
            start = self.find_tile(z,WorldTile.ascent_point)
            end = self.find_tile(z,WorldTile.exit_point)
        else:
            start = self.find_tile(z,WorldTile.ascent_point)
            end = self.find_tile(z,WorldTile.descent_point)

        return start, end

    def gen_feature(self,feature):
        if feature=='s_curve':
            pass
        elif feature=='dead_end':
            pass

    def build_rooms(self):
        """ Builds rooms off of the paths """
        pass

    def test_paths(self):
        """ Confirms each waypoint is reachable """
        pass
