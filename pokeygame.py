#!/usr/bin/env python2.7
## -*- coding: utf-8 -*-

# Built-in modules
import logging
import time
import curses
import sqlite3
import os
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

        for item in [
                    ('test_mode',False),
                    ('turn',0),
                    ('time_paused',0),
                    ('paused',False)
                    ]:
            setattr(self,*item)

        try:
            log_path = 'tmp/game_log.txt'
            os.stat(log_path)
        except OSError:
            pokeyworks.mkdir('tmp')

        self.logger = fw.setup_logger(
                                      self.name,
                                      self.log_lvl,
                                      'tmp/game_log.txt'
                                      )

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

    def show_menu(self):
        """ Main menu control function to be run in the curses wrapper """
        curses.curs_set(0)
        self.main_menu.display()

    def start_game(self):
        self.time_game_start = time.clock()
        self.logger.info("[*] Starting Game")
        curses.wrapper(self.show_menu)

    def play(self,screen):
        self.main_menu = PokeyMenu(MenuConfig(self,0),scrn)
        self.world_menu = PokeyMenu(MenuConfig(self,1),scrn)
        self.map_size_menu = PokeyMenu(MenuConfig(self,2),scrn)
        self.stdscreen = screen
        self.show_menu()


    def config_init(self):
        """ Pulls certain values, if they exist, from the game config """

        game_opts = [

            # Execution Options
            ('debug',False),             # Toggle Debug Messaging
            ('log_path',False),          # Turn on logging (w/path)
            ('log_lvl',logging.DEBUG),   # Set log level

            # World Generation Options
            ('flex_limit',3)             # Sets the maximum variance

            ]

        # Attempts to pull each value from the configuration
        # if not in config, the default value defined above
        # is set instead
        for opt in game_opts:
            try:
                setattr(self,opt[0],getattr(self.conf,opt[0]))
            except:
                setattr(self,opt[0],opt[1])
                continue

    def handle_error(self,e):
        """ Basic exception handling,rollbacks, and etc """

        if self.mode=='debug':
            raise e
        else:
            if e is KeyboardInterrupt or e is SystemExit:
                if raw_input('Really quit? (y quits)').upper()=='Y':
                    self.failsafe()
                    sys.exit(0)
            else:
                e_string = '[*] Game Error {0}:{1}'.format(type(e),e)
                self.logger.error(e_string)
                self.failsafe()
                sys.exit(1)

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

    def failsafe(self,e=None):
        """ Game failsafe, reverts to original state, discards
        changes to the database and/or files, closes any open
        files or connections """

        try:
            self.dbcon.close()
            print "\tThe database connection was killed"
        except:
            pass

    def db_con_open(self):

        #print fw.resource_path(self.conf.database_path[0])

        self.dbcon = sqlite3.connect(fw.resource_path(
                                        self.conf.database_path[0]))

    def db_con_close(self):
        self.cursor.close()
        self.dbcon.close()

    def db_execute(self,str_sql):
        """ Runs the passed SQL command against the database and
        returns the resulting dataset or return code """

        if self.dbcon:
            return self.dbcon.execute(str_sql)
        else:
            raise AssertionError('Database not connected!')
            return False

    def curses_print_map(self):
        """ Prints the map grid (Starts on floor 1) """
        map_window = self.stdscreen.subwin(5,5)
        map_keypad = map_window.keypad(1)
        map_panel = panel.new_panel(map_window)

        map_panel.update_panels()
        map_panel.top()
        map_panel.show()
        map_window.clear()

        x = 0; y=0; z=0

        # Print map phase
        draw_map(self,[x,y,z])

        def draw_map(game,loc):
            grid = game.grid

            z = loc[2]      # Load the current floor (z)

            for x in range(game.conf.x_dim[0]):
                for y in range(game.conf.y_dim[0]):
                    # Draw a map here!
                    pass

class WorldTile(object):

    """ Class to contain world tile objects """

    wall = '0'
    hallway = '1'
    door = '2'
    dungeon = '3'
    shop = '4'
    boss = '5'

    entry_point = 'S'
    descent_point = 'D'
    exit_point = 'E'
    ascent_point = 'U'

    tile_set = [wall,hallway,door,dungeon,shop,boss,
                entry_point,descent_point,exit_point,
                ascent_point]

    def __init__(self,tile_name,tile_type,**kwargs):
        self.tile_name = tile_name
        self.tile_type = tile_type
        assert self.tile_type in WorldTile.tile_set,'Invalid Tile Type'

        # kwarg defaults
        for pair in [
                    ('eligibles',{}),   # Eligible item/mob/trap types   
                    ('visible',False),  # Sets tile map visibility
                    ('explored',False), # Tile explored flag
                    ('spawn_rate',False),# General contents spawn rate
                    ('locked',False),   # Locked status (doors only)
                    ('mobs',[]),        # List of contained mobs
                    ('corpses',[]),     # List of contained corpses
                    ('items',[]),       # List of contained items
                    ('traps',[])        # List of contained traps
                    ('description',''), # Tile description
                    ('traversable',True) # Traversable flag
                    ]:
            try:
                setattr(self,pair[0],kwargs[pair[0]])
            except:
                setattr(self,pair[0],pair[1])

        # Only allow locking if the tile is a door
        if self.tile_type != WorldTile.door:
            assert not self.locked, 'Invalid tile to lock:{0}'.format(
                                                            self.tile_type
                                                            )

        self.tile_initialize(game)

    def tile_initialize(self,game):
        for item in ['mobs','items','traps']:
            self.gen(item)

    def gen(self,game,tile_content):
        for item_type in self.eligibles:
            if item_type==tile_content:
                possibles = self.eligibles[item_type]

        self.level = game.player.level
        item_list = getattr(self,item_type)
        succ,bonus = RandomRoll(game.player,self,self.spawn_rate)

        if succ and bonus:
            repetitions = 2
        elif succ:
            repetitions = 1
        else:
            repetitions = 0

        while repititions > 0:
            # Instantiates and appends the item_type
            item_list.append(possibles[random.randint(len(possibles))]())
            repetitions -= 1

class MenuConfig(object):

    """ Curses Menu configuration class """

    main_menu = 0
    world_menu = 1
    map_size_menu = 2

    def __init__(self,game,menu_type):

        if menu_type==MenuConfig.main_menu:
            # Main menu options
            return_items = [
                ('start game',game.play),
                ('world generation menu',game.world_menu.display)
                ]

        elif menu_type==MenuConfig.world_menu:
            # World Generation Options
            return_items = [
                ('set map size',game.map_size_menu.display,None),
                ('generate_map',game.generate_map),
                ('print map',game.curses_print_map),
                ('main menu',game.main_menu.display)
                ]
        elif menu_type==MenuConfig.map_size_menu:
            # Set x / y / z Parameters
            return_items = [
                ('set x ({0})'.format(game.conf.dim_x[0]),game.set_x),
                ('set y ({0})'.format(game.conf.dim_y[0]),game.set_y),
                ('set z ({0})'.format(game.conf.dim_z[0]),game.set_z),
                ('back',game.world_menu.display)
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
            return {(0,0,0):False} # Return grid dict

class Skill(object):

    """ Generic Skill Class """

    general_type=0
    combat_type=1
    stealth_type=2
    magic_type=3

    def __init__(self,name,skill_type):

        self.name = name
        self.skill_type = skill_type
        self.level = 1

    def assign(self,player,hcp):
        """ Assigns the skill an initial value based on the
        player class archetype chosen (by the hcp parameter)
        Invoked in the PlayerClass init phase """

        # Higher hcp = higher bonus potention (max 100)
        assert hcp <= 100, 'Skill handicap cannot be >100 hcp : {0}'.format(
                                                                        hcp)

        if self.level is not None:
            base,bonus = RandomRoll(player,self,hcp)

            if base and bonus:
                self.level += random.randint(3)+1
            elif base:
                self.level += random.randint(2)

    def increase(self,player):
        """ Chance of bonus skill point """

        if self.level is not None:
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

        else:
            return None

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
        if (self.roll/upper_bound) > (1-crit_range):
            self.crit=True
        else:
            self.crit=False

        if self.roll >= difficulty:
            self.hit=True
        else:
            self.hit=False

        return self.hit, self.crit

class Player(object):

    """ General Player class """

    male = 0
    female = 1

    def __init__(
                self,
                skill_list,
                p_name,
                p_age=27,
                p_sex=0
                ):

        self.name = p_name
        self.age = p_age
        self.sex = p_sex

        self.level=1
        self.crit_level=1
        self.turn = 0

        # Numeric attributes
        for item in [
                    'attack',
                    'defense',
                    'focus',
                    'resist_fire',
                    'resist_frost',
                    'resist_magic',
                    'resist_poison',
                    'resist_death'
                    ]:
            setattr(self,item,0)

        # Boolean attributes
        for bitem in [
                    'blind',
                    'paralyzed',
                    'slow',
                    'haste',
                    'berzerk',
                    'protected',
                    'immune',
                    'invincible'
                    ]:
            setattr(self,bitem,False)

        self.effects = []

        try:
            self.skills = [skill() for skill in skill_list]
        except:
            self.skills = skill_list

    def player_creation(self):
        """ Player creation script """

    def level_up(self):
        """ Levels up the player, increasing attributes """
        pass

    def process_effects(self):
        """ Processes assigned effects """

        for eff in self.effects:
            if eff.expires < self.turn:
                eff.expired = True
            else:
                args = {
                        'dmg':eff.apply_effect(self)+eff.delta,
                        'resist':eff.resist,
                        'dmg_attr':eff.attr
                        }

                self.proc_dmg_effect(**args)

        self.effects = [e for e in self.effects if not e.expired]

    def proc_dmg_effect(
                        self,
                        dmg_attr='health',
                        resist=None,
                        dmg=0,
                        percent=False
                        ):
        """ Processes player damage effects and resists """

        # If a resist attribute is passed, the player
        # will attempt to resist the damage
        if resist is not None:
            succ,bonus = RandomRoll(
                                    self,
                                    getattr(self,resist),
                                    75
                                    )
        else:
            succ = bonus = False

        # If the resist roll hits the bonus criteria, no damage
        if succ and bonus:
            dmg = 0

        # If the resist is successful but does not bonus
        # the damage is reduced by 50%
        elif succ:
                dmg = dmg/2

        att_value = getattr(self,dmg_att)

        if percent:
            # Convert dmg to a percentage and deduct from attribute
            p = dmg/100
            setattr(self,dmg_att,att_value-(p*att_value))
        else:
            setattr(self,dmg_att,getattr(self,dmg_att)-dmg)

    def proc_status_effect(
                            self,
                            status_att=None,
                            status_val=False,
                            resist=None
                            ):
        """ Processes player status effects and resists """

        # If a resist attribute is passed, the player
        # will attempt to resist the status change

        if resist is not None:
            succ,bonus = RandomRoll(
                                    self,
                                    getattr(self,resist),
                                    75
                                    )
        else:
            succ = False

        if succ:
            pass
        else:
            setattr(self,status_att,status_val)

class ColorIze(object):
    """ Allows colorizing (in available terminals)"""

    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    def __init__(self,val,opts):
        """ Takes the val, and wraps it in the passed opts """

        assert isinstance(opts,(list,tuple)), 'Invalid color option list!'

        retval = ''
        for opt in opts:
            retval += opt

        retval += '{}{}'.format(val,ColorIze.END)

        self.colorized = retval

        return

class StatusEffect(object):
    """ Temporary status effects on players """

    def __init__(
                self,
                se_name,
                se_attr,
                se_delta,
                expires=None,
                proc=None,
                proc_args={},
                rate=None
                ):

        self.name = se_name     # StatusEffect name
        self.attr = se_attr     # Attribute to be altered
        self.delta = se_delta   # Amount of damage(or bonus)
        self.proc = proc        # Additional proccessed effects
        self.expires = expires  # Sets expiration turn
        self.expired = False    # Expiration flag

    def apply_effect(self,player):
        self.level = player.level
        succ,crit = RandomRoll(player,self,rate)

        # If a status effect has an additional proc'ed effect,
        # a critical roll success is necessary to trigger it
        # The player might still resist
        if crit:
            if self.proc is not None:
                proc = self.proc
                proc(**self.proc_args)

        return self.process_apply(succ,crit)

    def process_apply(self,succ,crit):
        """ Takes the random roll output and returns the bonus amt """

        if succ and crit:
            bonus = 2
        elif succ:
            bonus = 1
        else:
            bonus = 0

        return bonus

class PlayerClass(object):

    """ Player class archetypes  """
    mage = 0
    fighter = 1
    rogue = 2

    def __init__(self,player,cl_type=1):
        self.type = cl_type

        # Assigns the skill an initial value based on
        # the selected archetype
        for skill in player.skills:
            if skill.skill_type==Skill.combat_type:
                skill.assign(player,100)
            elif skill.skill_type==Skill.magic_type:
                skill.assign(player,0)
            else:
                skill.assign(player,25)
