#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import math
import random
import sys
import pokeygame
import argparse
import inspect
import logging
import time
from pokeygame import ColorIze as color
from pokeygame import WorldTile
from pokeyworks import setup_logger as logger

class WorldGenerator(object):

    """ Generates worlds based on the config parameters """

    def __init__(
                self,           # The World Generator object
                debug=False,    # Debug mode
                silent=False,   # Silent mode
                rand=False,     # Random mode
                fpath=None,     # Output file path
                conf=None,      # Config file path
                dim_x=25,       # x dimension range
                dim_y=25,       # y dimension range
                dim_z=3,        # z dimension range
                flex_limit=0,   # Maximum dimension fluctuation
                verbose=False,  # Verbose mode
                app_logger=None # Optional passed logger
                ):
        """ WorldGenerator creates a world_generation_template """

        start = time.clock()

        if app_logger is None:
            # Enable verbose messages if in debug or verbose mode
            if debug or verbose:
                log_level = logging.DEBUG
            elif silent:
                log_level = logging.ERROR
            else:
                log_level = logging.INFO
            # Engage the logger
            self.logger = logger(__name__,log_level)
            self.logger.info('[*] WorldGenerator logger engaged')
        else:
            self.logger = app_logger
            self.logger.info('[*] Logger received')


        # Designate bottom floor as boss level
        self.boss_level = dim_z     # Boss on lowest level
        self.logger.debug('\tBoss on {}'.format(self.boss_level))

        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z

        self.min_dist = int(((self.dim_x+self.dim_y)/2)*.75)   #3/4 the avg
        self.logger.debug(
                '\tMinimum waypoint distance : {}'.format(self.min_dist)
                )

        self.grid = self.erect_walls()    # fill the dict with walls
        self.dims = (dim_x,dim_y,dim_z)
        self.logger.debug(
                '\tDimensions (x,y,z): ( {}, {}, {} )'.format(*self.dims)
                )

        # Map Generation Functions
        self.logger.info('[*] Generating map template')

        self.logger.info('[*] Generating waypoints')
        self.set_entry_point()
        self.set_descent_point()
        self.set_exit_point()

        self.logger.info('[*] Filling map content')
        self.build_paths()
        self.build_rooms()

        self.logger.info('[*] Testing map pathing')
        self.test_paths()

        self.logger.info('[*] Map generation complete')
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def __str__(self):
        retval = ''
        for z in range(0,self.dim_z+1):
            retval+='\tFloor -{0}-\n'.format(z)
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    if self.grid[x,y,z]=='0':
                        retval += '. '
                    else:
                        retval+= '.{0}'.format(self.grid[x,y,z])
                retval+='\n'

        return retval

    def erect_walls(self):
        grid = {}

        start = time.clock()
        self.logger.info('[*] Building walls')

        for z in range(0,self.dim_z+1):
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    grid[x,y,z]=WorldTile.wall

        self.logger.debug('\tFilled {} tiles'.format(len(grid)))
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

        return grid

    def set_entry_point(self):
        """ Sets the initial entry point on the map edge """

        start = time.clock()
        self.logger.info('[*] Setting entry point')

        z = 0   # Entry point is on first floor
        valid_x = range(1,self.dim_x-1) # valid values (OR w/valid_y)
        valid_y = range(1,self.dim_y-1)

        self.logger.debug('\tvalid_x range : {}'.format(valid_x))
        self.logger.debug('\tvalid_y range : {}'.format(valid_y))

        iterations = 0
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
                self.grid[x_test,y_test,z]=color(
                                            WorldTile.entry_point,
                                            [color.GREEN,color.BOLD],
                                            ).colorized
                self.start = (x_test,y_test,z)
                self.logger.debug('\tEntry point set : {0}'.format((
                                                        x_test,y_test,z
                                                        )))
                break
            iterations += 1

        self.logger.debug('\tEntry point took {} attempts'.format(iterations))
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def set_descent_point(self):
        """ Sets point to descend/ascend on each level """

        self.logger.info('[*] Setting descent points')
        start = time.clock()

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
                self.grid[x_test,y_test,i]=color(
                                    WorldTile.descent_point,
                                    [color.CYAN,color.BOLD],
                                    ).colorized
                self.logger.debug(
                       '\tDescent Point Set {0}'.format((x_test,y_test,i))
                       )

                # Add corresponding ascent point on the next floor
                self.grid[x_test,y_test,i+1]=color(
                                    WorldTile.ascent_point,
                                    [color.RED,color.BOLD],
                                    ).colorized
                self.logger.debug(
                       '\tAscent Point Set {0}'.format((x_test,y_test,i+1))
                       )
                i += 1

        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def path_avail_dirs(self,position,impediments,dest=None,rand=False):
        # Processes available directions, returns a random direction
        # if the random flag is passed, else returns the direction
        # list

        self.logger.debug('[*] Finding available directions')

        imp = ''.join(str(i) for i in impediments)
        self.logger.debug('\tImpediments : {}'.format(imp))

        p = position
        self.logger.debug('\tPosition : {}'.format(p))

        # Define directions
        north = [0,1]
        south = [0,-1]
        east = [1,1]
        west = [1,-1]

        if dest is not None:
            prefer_y = [True] if p[0]==dest[0] else [False]
            prefer_x = [True] if p[1]==dest[1] else [False]

            if p[0]<dest[0] and prefer_x: prefer_x.append(1)
            if p[0]>dest[0] and prefer_x: prefer_x.append(-1)
            if p[1]<dest[1] and prefer_y: prefer_y.append(1)
            if p[1]>dest[1] and prefer_y: prefer_y.append(-1)

            # Reduce compared value for more direct paths
            if random.randint(0,100)>30:
                apply_preference=True
            else:
                apply_preference=False

        # impediments will contain impassable vals
        # x-axis
        if p[0]+1>=self.dim_x:
            north.append(False)
        else:
            north.append(
                True if self.grid[p[0]+1,p[1],p[2]] not in imp else False
                )

        if p[0]-1<=0:
            south.append(False)
        else:
            south.append(
                True if self.grid[p[0]-1,p[1],p[2]] not in imp else False
                )

        # y-axis
        if p[1]+1>=self.dim_y:
            east.append(False)
        else:
            east.append(
                True if self.grid[p[0],p[1]+1,p[2]] not in imp else False
                )
        if p[1]-1<=0:
            west.append(False)
        else:
            west.append(
                True if self.grid[p[0],p[1]-1,p[2]] not in imp else False
                )

        dirs = [north,south,east,west]
        assert any(dirs),'Pathbuilder : No available moves!'

        if not rand:
            return dirs
        elif apply_preference and (prefer_x or prefer_y):
            if prefer_x[0]:
                self.logger.debug('\tPreferring x : {}'.format(prefer_x[1]))
                return 0,prefer_x[1]
            elif prefer_y:
                self.logger.debug('\tPreferring y : {}'.format(prefer_y[1]))
                return 1,prefer_y[1]
        else:
            # Randomly selects an available move and returns it
            while True:
                roll = random.randint(0,3)
                dirs = [north,south,east,west]
                if dirs[roll][2]:
                    if roll in [0,1]:
                        idx = 0
                        val = 1 if roll==0 else -1
                    else:
                        idx = 1
                        val = 1 if roll==2 else -1
                    break

            self.logger.debug('\tindex (x,y)= {} value= {}'.format(idx,val))
            return idx,val

    def calc_dist(self,pt1,pt2):
        x_term = pt1[0]-pt2[0]
        y_term = pt1[1]-pt2[1]
        return math.sqrt(x_term**2+y_term**2)

    def find_tile(self,z,tile_type):
        """ Looks for the given tile type on the requested floor """
        retval = False
        for y in range(self.dim_y):
            for x in range(self.dim_x):
                try:
                    if tile_type in self.grid[x,y,z]:
                        retval = (x,y,z)
                except TypeError:
                    if self.grid[x,y,z]==tile_type:
                        retval = (x,y,z)
        return retval

    def set_exit_point(self):
        """ Sets exit point on the map edge, far enough from entry """

        valid_x = range(1,self.dim_x-1)
        valid_y = range(1,self.dim_y-1)
        max_attempts = 500
        this_attempt = 0

        self.logger.info('[*] Setting exit point')
        self.logger.debug('\tvalid_x range : {}'.format(valid_x))
        self.logger.debug('\tvalid_y range : {}'.format(valid_y))

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
                self.logger.debug('\tAscent point found : {}'.format(asc))
                test = (x_test,y_test,self.dim_z)
                if self.calc_dist(asc,test)>=self.min_dist:
                    self.grid[test]=color(
                                    WorldTile.exit_point,
                                    [color.GREEN,color.BOLD],
                                    ).colorized
                    self.end = test
                    self.logger.debug(
                           '\tExit Point Set {0}'.format(tuple(test)
                           ))
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
        self.logger.debug(
            '\tWaypoint density : {0}'.format(waypoints_per_floor)
            )
        way_list = self.build_waypoints(waypoints_per_floor)

        for i in range(len(way_list)-1):
            way1 = way_list[i]
            way2 = way_list[i+1]

            # If the two waypoints are on the same floor,
            # connect them
            if way1[2]==way2[2]:
                self.logger.info('[*] Connecting {0} to {1}'.format(way1,way2))
                self.connect(way1,way2)

    def connect(self,pt1,pt2):
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

        max_loops = 30      # Max loops per leg
        this_loop = 0

        while True:
            # Pathbuilder exit conditions:
            if this_loop >= max_loops:
                self.logger.debug('\tMaximum steps for this leg (pathbuilder)')
                break
            if tuple(coord_list)==pt2:
                # Arrived at destination waypoint
                self.logger.debug('\tArrived at point {}'.format(pt2))
                break

            # Final leg detector - executes when a point is reached
            # on the same axis (x/y) and within 2 tiles.  Directly
            # connects to the endpoint
            if coord_list[0]==pt2[0] and abs(coord_list[1]-pt2[1])<3:
                idx = 1     # axis of motion = x
                rng = coord_list[1]-pt2[1]
            elif coord_list[1]==pt2[1] and abs( coord_list[0]-pt2[0])<3:
                idx = 0     # axis of motion = x
                rng = coord_list[0]-pt2[0]
            else:
                rng = False

            if rng:
                self.logger.debug('\tDestination point in range')
                for n in range(rng):
                    coord = coord_list
                    coord[idx]+=n
                    coord = tuple(coord)
                    assert isinstance(coord,(tuple)), 'Invalid coord {}'.format(
                                                                    coord
                                                                    )
                    tile_list.append(coord)
                break
            # If not the final leg, randomly select a direction
            idx,val = self.path_avail_dirs(
                                coord_list,
                                ['1','E','U','D'],
                                pt2,
                                True)
            coord_list[idx]+=val
            tile_list.append(tuple(coord_list))
            this_loop +=1

        # Fill the resulting point list with hallways in the grid
        for tile in tile_list:
            try:
                if self.grid[tile]==WorldTile.wall:
                    self.grid[tile]=color(
                                    WorldTile.hallway,
                                    [color.BLUE,color.BOLD],
                                    ).colorized
            except KeyError:
                self.logger.error('[*] Invalid tile specified!')
                self.logger.debug('Tile value : {}'.format(tile))
                continue

    def build_waypoints(self,w):
        retval = []
        for z in range(self.dim_z+1):
            # Set starting waypoint for the floor
            if z == 0:
                retval.append(self.start)
            else:
                retval.append(self.find_tile(z,WorldTile.ascent_point))

            # Fill other waypoints
            dbg_string = 'Floor {} waypoints :\n\t'.format(z)
            for way in range(w):
                x = random.randint(1,self.dim_x-1)
                y = random.randint(1,self.dim_y-1)

                if len(retval)%4==0:
                    dbg_string += '{}\n\t'.format((x,y,z))
                else:
                    dbg_string += '{0},'.format((x,y,z))

                retval.append((x,y,z))
            dbg_string = dbg_string[:-1]
            self.logger.debug(dbg_string)

            # Set ending waypoint for the floor
            if z == self.dim_z:
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

        for z in range(0,self.dim_z):
            start, end = self.find_path_ends(z)
            for pt in (start,end):
                self.create_room(WorldTile.dungeon,pt,3)


    def create_room(self,fill,center,size=None):
        """ Creates a rectangle in the approximate size passed, None = random """

        if size is None:
            size = random.randint(2,int((self.dimx+self.dimy)/2))

        # Replaces tile contents in a square around the center with fill
        for s in range(1,size):
            this_point = list(center)
            for idx in [0,1]:
                for val in [s,-s]:
                    try:
                        this_point[idx] += val
                        self.grid[tuple(this_point)] = fill
                    except KeyError:
                        continue
                    except:
                        raise

    def test_paths(self):
        """ Confirms each waypoint is reachable """
        pass

class CLInvoker(object):
    """ Class to handle command line execution """

    def __init__(self):

        if '-d' in sys.argv or '--debug' in sys.argv or \
           '-v' in sys.argv or '--verbose' in sys.argv:

            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        self.logger = logger(__name__,log_level)
        self.logger.info('[*] Command-line invoker engaged')

        try:
            self.handle_args()
            start = time.clock()
            self.world = WorldGenerator(
                        self.args.debug,self.args.silent,self.args.random,
                        self.args.fpath,self.args.conf,self.args.xdim,
                        self.args.ydim,self.args.zdim,self.args.elastic,
                        self.args.verbose,self.logger
                        )
            self.logger.debug('\tWorld generation took {}s'.format(
                                                        time.clock()-start
                                                        ))
            while True:
                self.menu()

        except (KeyboardInterrupt,SystemExit):
            sys.exit(0)

    def menu(self):
        """ Main menu """

        menu_items = [
                ('Show [m]ap','m',self.show_map),
                ('[R]egenerate','r',self.regenerate),
                ('[S]ave ({})'.format(self.args.fpath),'s',self.save_map),
                ('[Q]uit','q',sys.exit)
                ]

        for n in range(len(menu_items)):
            print '{}. {}'.format(n,menu_items[n][0])

        ch = raw_input('Selection > ')

        if ch.lower() not in [item[1] for item in menu_items]:
            print 'Invalid selection : ', ch.lower()
            raw_input('Press any key to continue (Ctrl+C exits)')
        else:
            for item in menu_items:
                if ch.lower()==item[1]:
                    item[2]()

    def show_map(self):
        print self.world

    def regenerate(self):
        try:
            self.world = WorldGenerator(
                       self.args.debug,self.args.silent,self.args.random,
                       self.args.fpath,self.args.conf,self.args.xdim,
                       self.args.ydim,self.args.zdim,self.args.elastic,
                       self.args.verbose,self.logger
                       )
        except TypeError:
            self.world = WorldGenerator()

    def save_map(self):
        """ Saves the map template to a python file, as a 2-tuple """

        self.logger.info('[*] Saving map template')

        o = 'map_template = (\n'
        for z in range(int(self.args.zdim)-1):
            o += '\t\t(\n'
            for y in range(int(self.args.ydim)-1):
                o += '\t\t\t('
                tmp = ''
                for x in range(int(self.args.xdim)-1):
                    tmp += '{},'.format(self.world.grid[x,y,z])
                o += tmp[:-1]
                o += '),\n'
            o += '\t\t),\n'

        o += '\t)\n'

        try:
            with open(self.args.fpath,'w') as outfile:
                outfile.write(o)
        except:
            self.logger.error('\tFile write failed to {} '.format(
                                                   self.args.fpath
                                                   ))
        else:
            self.logger.debug('\tFile written successfully to {}'.format(
                                                        self.args.fpath
                                                        ))
            self.logger.debug('\tList variable = map_template')

    def handle_args(self):

        parser = argparse.ArgumentParser()
        self.logger.info('[*] Handling command line arguments')

        # Arg_list : [0]=short arg, [1]=long arg, [2]=help msg,
        #            [3]=store_true/false, [4]=default, [5]=nargs
        arg_list =  [
            ("-d","--debug","enable debug mode",'store_true'),
            ("-s","--silent","silent mode (no output)",'store_true'),
            ("-r","--random","generates a randomized map",'store_true'),
            ("-f","--fpath","specify output file",None,'world_gen_output.py',1),
            ("-c","--conf","specify conf file",None,'world_gen.conf',1),
            ("-x","--xdim","map x dimension",None,25,1),
            ("-y","--ydim","map y dimension",None,25,1),
            ("-z","--zdim","map floor depth",None,3,1),
            ('-e','--elastic','specify flexible dimensions',None,3,1),
            ('-v','--verbose','enable verbose messages','store_true')
            ]

        # Parse Flags (boolean)
        self.logger.debug('\tAdding boolean flags')
        for f in [arg for arg in arg_list if arg[3] is not None]:
            parser.add_argument(f[0],f[1],help=f[2],action=f[3])

        # Parse Parameters (values)
        self.logger.debug('\tAdding parameters')
        for p in [arg for arg in arg_list if arg[3] is None]:
            parser.add_argument(p[0],p[1],help=p[2],default=p[4],nargs=p[5])

        self.logger.debug('\tParsing arguments')
        self.args=parser.parse_args()

if __name__=='__main__':
    CLInvoker()
