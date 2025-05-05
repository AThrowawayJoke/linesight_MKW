"""
This file contains classes that facilitate passing game data from the instance hook to the game manager.
As the game_instance_hook.py file runs within dolphin, it has access to the functions defined in the dolphin stubs.
Due to this, the game manager cannot import the classes which define datatypes for the game.
Thus, this file copies implementations of mat34 and vec3 without using dolphin stubs, and defines TypedDicti classes to assist data transfer.


"""

from dataclasses import dataclass
import math
from typing import TypedDict
import os, sys
sys.path.append(os.path.expanduser("~") + "\\AppData\\Local\\programs\\python\\python312\\lib\\site-packages")
import flatdict
from config_files import config_copy

@dataclass
class mat34:
    e00: float = 0.0
    e01: float = 0.0
    e02: float = 0.0
    e03: float = 0.0
    e10: float = 0.0
    e11: float = 0.0
    e12: float = 0.0
    e13: float = 0.0
    e20: float = 0.0
    e21: float = 0.0
    e22: float = 0.0
    e23: float = 0.0

@dataclass
class vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def length_xz(self) -> float:
        return math.sqrt(self.x**2 + self.z**2)

class SurfaceProperties():
    def __init__(self, value):
        self.value = value

    WALL = 0x1
    SOLID_OOB = 0x2
    BOOST_RAMP = 0x10
    OFFROAD = 0x40
    BOOST_PANEL_OR_RAMP = 0x100
    TRICKABLE = 0x800

class Boosts(TypedDict, total=False):
    mt_charge: int
    smt_charge: int # smt exclusive to karts
    ssmt_charge: int
    mt_boost: int
    trick_boost: int
    shroom_boost: int

class Kart_Data(TypedDict, total=False):
    position: vec3
    part_rotation: mat34
    angle: float

    external_velocity: vec3
    internal_velocity: vec3
    moving_road_velocity: vec3
    moving_water_velocity: vec3

    wheelie_cooldown: int
    trick_cooldown: int

class Race_Data(TypedDict, total=False):
    lap_completion: float
    race_completion: float
    race_completion_max: float
    checkpoint_id: int
    current_key_checkpoint: int
    max_key_checkpoint: int

    respawn_point: int
    driving_direction: int # 0, 1, 2, or 3.
    item_count: int
    item_type: int



class Game_Data(TypedDict, total=False):
    boost_data: Boosts
    kart_data: Kart_Data
    race_data: Race_Data

    start_boost_charge: float
    trickable_timer: int
    surface_properties: SurfaceProperties
    airtime: int

float_input_mean = [
    0.5, # A
    0.1, # B
    0.1, # Dpad Up
    113, # StickX
    113, # StickY
    0.5, # TriggerLeft
    0.5, # TriggerRight
    0.5, # A
    0.1, # B
    0.1, # Dpad Up
    113, # StickX
    113, # StickY
    0.5, # TriggerLeft
    0.5, # TriggerRight
    0.5, # A
    0.1, # B
    0.1, # Dpad Up
    113, # StickX
    113, # StickY
    0.5, # TriggerLeft
    0.5, # TriggerRight
    0.5, # A
    0.1, # B
    0.1, # Dpad Up
    113, # StickX
    113, # StickY
    0.5, # TriggerLeft
    0.5, # TriggerRight
    0.5, # A
    0.1, # B
    0.1, # Dpad Up
    113, # StickX
    113, # StickY
    0.5, # TriggerLeft
    0.5, # TriggerRight
    # End ugly ugly input listing
    75, # mt_charge
    20, # smt_charge
    3, # ssmt_charge
    30, # mt_boost
    0, # trick_boost
    30, # shroom_boost
    100000.0, # position.x
    10000.0, # position.y
    100000.0, # position.z
    0.0, # angle
    40.0, # external_velocity.x
    10.0, # external_velocity.y
    40.0, # external_velocity.z
    60.0, # internal_velocity.x
    10.0, # internal_velocity.y
    60.0, # internal_velocity.z
    0.0, # moving_road_velocity.x
    0.0, # moving_road_velocity.y
    0.0, # moving_road_velocity.z
    0.0, # moving_water_velocity.x
    0.0, # moving_water_velocity.y
    0.0, # moving_water_velocity.z
    5, # wheelie_cooldown
    5, # trick_cooldown
    0.5, # lap_completion
    2.0, # race_completion
    2.0, # race_completion_max
    10, # checkpoint_id
    3, # current_key_checkpoint
    3, # max_key_checkpoint
    2, # driving_direction
    1, # item_count
    0.01, # start_boost_charge -- average value over an entire rollout
    2, # trickable_timer
    2, # surface_properties
    10, # airtime
]

float_input_deviation = [
    1, # A
    1, # B
    1, # Dpad Up
    255, # StickX
    255, # StickY
    1, # TriggerLeft
    1, # TriggerRight
    1, # A
    1, # B
    1, # Dpad Up
    255, # StickX
    255, # StickY
    1, # TriggerLeft
    1, # TriggerRight
    1, # A
    1, # B
    1, # Dpad Up
    255, # StickX
    255, # StickY
    1, # TriggerLeft
    1, # TriggerRight
    1, # A
    1, # B
    1, # Dpad Up
    255, # StickX
    255, # StickY
    1, # TriggerLeft
    1, # TriggerRight
    1, # A
    1, # B
    1, # Dpad Up
    255, # StickX
    255, # StickY
    1, # TriggerLeft
    1, # TriggerRight
    # End ugly ugly input list
    270, # mt_charge
    270, # smt_charge
    75, # ssmt_charge
    141, # mt_boost
    100, # trick_boost
    90, # shroom_boost
    250000.0, # position.x
    25000.0, # position.y
    250000.0, # position.z
    180.0, # angle -- assumption, also assuming this value even helps
    120.0, # external_velocity.x
    120.0, # external_velocity.y
    120.0, # external_velocity.z
    120.0, # internal_velocity.x
    120.0, # internal_velocity.y
    120.0, # internal_velocity.z
    # Toad's factory conveyers
    120.0, # moving_road_velocity.x
    120.0, # moving_road_velocity.y
    120.0, # moving_road_velocity.z
    # Koopa Cape's water stream
    120.0, # moving_water_velocity.x
    120.0, # moving_water_velocity.y
    120.0, # moving_water_velocity.z
    20, # wheelie_cooldown
    30, # trick_cooldown
    1.0, # lap_completion
    4.0, # race_completion
    4.0, # race_completion_max
    100, # checkpoint_id
    15, # current_key_checkpoint
    15, # max_key_checkpoint
    4, # driving_direction
    3, # item_count
    1.0, # start_boost_charge
    23, # trickable_timer
    5, # surface_properties
    240, # airtime -- note that this may be higher if you get more than 4 seconds of airtime but eh.
]

class Network_Inputs():
    def __init__(self, game_data: Game_Data, previous_actions_idx):
        self.game_data = game_data
        self.__flat_game_data = None
        self.previous_actions_idx = previous_actions_idx

    def get_input_dimensions(self):
        previous_inputs_length = config_copy.n_prev_actions_in_inputs * 18
        game_data_length = len(self.get_flattened_game_data())
        
        input_dimensions = previous_inputs_length + game_data_length
        # Sanity check in case of bad programmers
        assert game_data_length == len(float_input_deviation)
        return input_dimensions
    
    def get_input_data(self):
        previous_actions = [
            # Get inputs from k for every k that we have not processed yet
            config_copy.inputs[self.previous_actions_idx[k] if k >= 0 else config_copy.action_forward_idx]
            for k in range(
                len(self.previous_actions_idx) - config_copy.n_prev_actions_in_inputs, len(self.previous_actions_idx)
            )
        ]
        unwrapped_actions = []
        for dictionary in previous_actions:
            for value in dictionary.values():
                unwrapped_actions.append(value)
        
        return unwrapped_actions

    def get_flattened_game_data(self):
        if not self.__flat_game_data:
            temp_game_data = self.game_data
            for key in temp_game_data["kart_data"].keys():
                value = temp_game_data["kart_data"][key]
                if type(value) == vec3:
                    temp_game_data["kart_data"][key] = [value.x, value.y, value.z]
            self.__flat_game_data = flatdict.FlatterDict(temp_game_data).values()
        return self.__flat_game_data
