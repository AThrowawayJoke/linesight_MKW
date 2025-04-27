from dataclasses import dataclass
import math
from typing import TypedDict

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

class Boosts(TypedDict):
    mt_charge: int
    smt_charge: int # smt exclusive to karts
    ssmt_charge: int
    mt_boost: int
    trick_boost: int
    shroom_boost: int

class Kart_Data(TypedDict):
    position: vec3
    part_rotation: mat34
    angle: float

    external_velocity: vec3
    internal_velocity: vec3
    moving_road_velocity: vec3
    moving_water_velocity: vec3

    wheelie_cooldown: int
    trick_cooldown: int

class Race_Data():
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



class Game_Data(TypedDict):
    boost_data: Boosts
    kart_data: Kart_Data
    race_data: Race_Data

    start_boost_charge: float
    trickable_timer: int
    surface_properties: SurfaceProperties
    airtime: int





