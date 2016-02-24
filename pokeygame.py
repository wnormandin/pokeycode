#!/usr/bin/env python2.7
## -*- coding: utf-8 -*-

# Built-in modules
import logging
import time
import curses
import sqlite3
from curses import panel

# Custom modules
import pokeyworks as fw
from pokeywins import PokeyMenu

class PokeyGame(object):
    """ The PokeyGame class is intended to be a SuperClass
    for basic terminal games.  Functionality is not
    guaranteed """
    
    def __init__(self,game_name,conf_path='pokeygame.conf'):
   
        # Game initialization 
        self.name = game_name
        self.conf = fw.PokeyConfig(conf_path)
        self.config_init()
        
        try:
            self.logger = fw.setup_logger(
                                          self.name,
                                          self.log_lvl,
                                          'tmp/game_log.txt'
                                          )
        except IOError:
            pokeyworks.mkdir('tmp')
            self.logger = fw.setup_logger(
                                          self.name,
                                          self.log_lvl,
                                          'tmp/game_log.txt'
                                          )
        
        self.time_paused = 0
        self.paused=False
        self.grid = GameGrid(self.conf)

    def toggle_pause(self,opt=None):
        """ Toggles the game's pause status, opt will allow the status
        to be set, or left alone if already correctly set """
        
        if opt is not None:
            if opt!=self.paused:
                if self.paused:
                    self.time_paused+=(time.clock()-self.pause_start)
                else:
                    self.pause_start=time.clock()
                self.paused = opt
        else:
            if self.paused:
                self.time_paused+=(time.clock()-self.pause_start)
            else:
                self.pause_start=time.clock()
            self.paused = not self.paused
            
        self.logger.info('[*] Pause = {0}'.format(self.paused))
        
    def main_menu(self,scrn):
        """ Main menu control function to be run in the curses wrapper """
        
        items = MenuConfig(self,MenuConfig.main_menu).menu_items
        curses.curs_set(0)
        PokeyMenu(items,scrn).display()
        
    def start_game(self):
        self.time_game_start = time.clock()
        self.logger.info("[*] Starting Game")
        curses.wrapper(self.main_menu)
        
    def play(self):
        pass
        
    def config_init(self):
        """ Pulls certain values, if they exist, from the game config """
        
        game_opts = [
        
            # Execution Options
            ('debug',False),             # Toggle Debug Messaging
            ('log_path',False),          # Turn on logging (w/path)
            ('log_lvl',logging.DEBUG),   # Set log level
            
            # World Generation Options
            ('flex_dims',False),         # Allows dims to fluctuate
            ('flex_limit',3)             # Sets the maximum variance
            
            ]
                
        for opt in game_opts:
            try:
                setattr(self,opt[0],getattr(self.conf,opt[0]))
            except:
                setattr(self,opt[0],opt[1])
                continue
                
    def handle_error(self,e):
        """ Basic exception handling,rollbacks, and etc """
        
        if self.mode=='debug':
            raise
        else:
            if e is KeyboardInterrupt or e is SystemExit:
                if raw_input('Really quit? (y quits)').upper()=='Y':
                    self.failsafe()
                    sys.exit(0)
            e_string = '[*] Game Error {0}:{1}'.format(type(e),e)
            self.logger.error(e_string)
            
    def load_game(self):
        """ Loads the various object files into the database """
        
        dat_list = [
                    'items'#,
                    #'skills',
                    #'mobs',
                    #'tiles',
                    #'classes'
                    ]
                    
        self.db_con_open()       
        for item in dat_list:
            item_path = '/'.join([
                            self.conf.dat_base_path[0],
                            '{}.dat'.format(item)
                            ])
                            
            with open(item_path,'rb') as datfile:
                header_row = datfile.readline().rstrip().split('%')
                str_sql = "CREATE TABLE {0}".format(item)
                str_sql += " ( id INTEGER PRIMARY KEY,"
                data_types = datfile.readline().rstrip('\n').split('%')
                allow_null = datfile.readline().rstrip('\n').split('%')
                
                for col in range(len(header_row)):
                    str_sql += ' {0} {1}'.format(
                                                    header_row[col],
                                                    data_types[col]
                                                    )
                                                    
                    if allow_null[col]=='0':
                        str_sql += ','
                    else:
                        str_sql += ' NOT NULL, '
                                                    
                str_sql = str_sql.strip(',')    # Trim the trailing comma
                str_sql += ');'
                
                print str_sql
                self.dbcon.execute(str_sql)
                file_data = datfile.readlines()
                
                for row in file_data:
                    row = row.rstrip('\n').split('%')
                    vals = ''
                    str_sql = 'INSERT INTO {0} '.format(item)
                    
                    for i in range(len(header_row)):
                        
                        if data_types[i]=='TEXT' and row[i] != 'NULL':
                            vals += '"{0}", '.format(row[i])
                        else:
                            vals += '{0}, '.format(row[i])
                            
                    vals = vals.rstrip(', ')
                        
                    str_sql += 'VALUES (NULL, {0});'.format(vals)
                    
                    print str_sql
                    self.dbcon.execute(str_sql)
                    self.cursor = self.dbcon.cursor()
        
        self.db_con_close()           

    def db_con_open(self):
        
        #print fw.resource_path(self.conf.database_path[0])
            
        self.dbcon = sqlite3.connect(fw.resource_path(
                                        self.conf.database_path[0]))
    
    def db_con_close(self):
        self.cursor.close()
        self.dbcon.close()
                
    def db_execute(self):
        pass
            
class MenuConfig(object):
    """ Curses Menu configuration class """
    
    main_menu = 0
    world_menu = 1
    
    def __init__(self,game,menu_type):
        
        if menu_type==MenuConfig.main_menu:
            # Main menu options
            return_items = [
                ('start game',game.play)
                ]
            
        elif menu_type==MenuConfig.world_menu:
            # World Generation Options
            return_items = [
                ('not implemented',curses.beep)
                ]
                
        else:
            game.handle_error(
                     AssertionError('Invalid Menu Type!:{0}'.format(menu_type))
                    )
            return_items = False
            
        self.menu_items = return_items
                   
class GameGrid(object):
    """ Basic grid to store tile objects, offers movement operations, 
    returning the tile at the resulting location """
    
    def __init__(self,conf):
    
        self.grid = self.grid_init_check(conf)
        
    def grid_insert(self,tile,loc):
        try:
            x,y,z = loc[0],loc[1],loc[2]
            self.grid[x,y,z]=tile
        except Exception as e:
            self.game.handle_error(e)
            return False
        else:
            
            return True
            
    def get_tile(self,loc):
        try:
            x,y,z = loc[0],loc[1],loc[2]
            return grid[x,y,z]
        except Exception as e:
            self.game.handle_error(e)
            return False
        
    def grid_init_check(self,conf):
        """ Verifies the given dimensions """
        try:
            assert isinstance(conf.dim_x[0],int),(
                'Bad dimension x:{0}'.format(conf.dim_x[0]))
            assert isinstance(conf.dim_y[0],int),(
                'Bad dimension y:{0}'.format(conf.dim_y[0]))
            assert isinstance(conf.dim_z[0],int),(
                'Bad dimension z:{0}'.format(conf.dim_z[0]))
        except AssertionError:
            return False
        else:
            return {(0,0,0):False} # Return grid dict initialized

class Skill(object):
    """ Generic Skill Class """
    
    general_type=0
    combat_type=1
    stealth_type=2
    magic_type=3
    
    def __init__(self):
        pass
        
    def increase(self,player):
        """ Chance of bonus skill point """
        
        increase_roll = (random.randint(0,player.level))
        
        if skill.level < (player.level/2):
            bonus_threshold = .5
        else:
            bonus_threshold = .75
            
        if increase_roll/player.level >= bonus_threshold:
            skill.level +=2
        else:
            skill.level +=1
            
        return skill.level

class RandomRoll(object):
    """ Performs various skill rolls involved in gameplay, lvl
    and player generation, and other generated attributes """
            
    def __init__(self,player,skill,difficulty):
        """ Takes attributes from the passed skill and difficulty
        to perform a roll and return an action """
      
        # Lowest possible skill roll == skill lvl - player lvl (or 0)
        lower_bound = max(0,skill.level - player.level)
         
        # Highest possible skill roll == skill lvl + 2*player level
        upper_bound = skill.level + (2*player.level)
                            
        # Sets critical range (upper percentile to be considered crit)
        crit_range = player.crit_level / 100
        
        self.roll = random.randint(lower_bound,upper_bound)
        if (self.roll/upper_bound) > crit_range:
            self.crit=True
        else:
            self.crit=False
            
        if self.roll >= difficulty:
            self.hit=True
        else:
            self.hit=False
        
        return self.hit, self.crit
