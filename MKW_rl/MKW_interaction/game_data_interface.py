"""
This file attempts to make interfacing with the game easier by containing the important information about the game
within directly callable functions in leiu of the instance manager program handling the static objects
"""

from mkw_scripts.Modules.mkw_classes.common import SurfaceProperties

import mkw_scripts.Modules.mkw_utils as mkw_utils
from mkw_scripts.Modules.mkw_classes import RaceManager, RaceManagerPlayer, RaceState
from mkw_scripts.Modules.mkw_classes import RaceConfig, RaceConfigScenario, RaceConfigSettings
from mkw_scripts.Modules.mkw_classes import KartObject, KartMove, KartSettings, KartBody
from mkw_scripts.Modules.mkw_classes import VehicleDynamics, VehiclePhysics, KartBoost, KartJump
from mkw_scripts.Modules.mkw_classes import KartState, KartCollide, KartInput, RaceInputState

class Game_Data_Interface():
	def __init__(self):
		"""
		All class objects can be initiated upon save state loading, when initialize_race_objects should be called
		All function calls return the current value, not the location in memory.
		"""
		self.race_mgr_player: RaceManagerPlayer
		self.race_scenario: RaceConfigScenario
		self.race_settings: RaceConfigSettings

		self.kart_object: KartObject
		self.kart_state: KartState
		self.kart_move: KartMove
		self.kart_body: KartBody
		self.kart_boost: KartBoost
		self.kart_collide:KartCollide
		self.kart_jump: KartJump

		self.vehicle_dynamics: VehicleDynamics
		self.vehicle_physics: VehiclePhysics

		"""if self.kart_move.is_bike:
			text += f"Wheelie Length: {self.kart_move.wheelie_frames()}\n"
			text += f"Wheelie CD: {self.kart_move.wheelie_cooldown()} | "
		"""

	def initialize_race_objects(self):
		self.race_mgr_player = RaceManagerPlayer()
		self.race_scenario = RaceConfigScenario(addr=RaceConfig.race_scenario())
		self.race_settings = RaceConfigSettings(self.race_scenario.settings())

		self.kart_object = KartObject()
		self.kart_state = KartState(addr=self.kart_object.kart_state())
		self.kart_move = KartMove(addr=self.kart_object.kart_move())
		self.kart_body = KartBody(addr=self.kart_object.kart_body())
		self.kart_boost = KartBoost(addr=self.kart_move.kart_boost())
		self.kart_collide = KartCollide(addr=self.kart_object.kart_collide())
		self.kart_jump = KartJump(addr=self.kart_move.kart_jump())

		self.vehicle_dynamics = VehicleDynamics(addr=self.kart_body.vehicle_dynamics())
		self.vehicle_physics = VehiclePhysics(addr=self.vehicle_dynamics.vehicle_physics())

	def get_start_boost_charge(self):
		return self.kart_state.start_boost_charge()
	
	def get_trickable_timer(self):
		return self.kart_state.trickable_timer()
	
	def get_boost_states(self):
		return {
			"mt_charge": self.kart_move.mt_charge(),
			"smt_charge": self.kart_move.smt_charge(), # smt exclusive to karts
			"ssmt_charge": self.kart_move.ssmt_charge(),
			"mt_boost": self.kart_boost.all_mt_timer(),
			"trick_boost": self.kart_boost.trick_and_zipper_timer(),
			"shroom_boost": self.kart_boost.mushroom_and_boost_panel_timer()
		}
	
	def get_kart_position_and_rotation(self):
		return {
			"position": self.vehicle_physics.position(),
			"rotation": self.kart_body.kart_part_rotation()
		}
	
	def get_kart_velocities(self):
		return {
			"external_velocity": self.vehicle_physics.external_velocity(),
			"internal_velocity": self.vehicle_physics.internal_velocity(),
			"moving_road_velocity": self.vehicle_physics.moving_road_velocity(),
			"moving_water_velocity": self.vehicle_physics.moving_water_velocity()
		}

	def get_surface_properties(self):
		"""
		surface_properties = self.kart_collide.surface_properties()

		self.is_wall = (surface_properties.value & SurfaceProperties.WALL) > 0
		self.is_solid_oob = (surface_properties.value & SurfaceProperties.SOLID_OOB) > 0
		self.is_boost_ramp = (surface_properties.value & SurfaceProperties.BOOST_RAMP) > 0
		self.is_offroad = (surface_properties.value & SurfaceProperties.OFFROAD) > 0
		self.is_boost_panel_or_ramp = (surface_properties.value & SurfaceProperties.BOOST_PANEL_OR_RAMP) > 0
		self.is_trickable = (surface_properties.value & SurfaceProperties.TRICKABLE) > 0

		WALL = 0x1
		SOLID_OOB = 0x2
		BOOST_RAMP = 0x10
		OFFROAD = 0x40
		BOOST_PANEL_OR_RAMP = 0x100
		TRICKABLE = 0x800
		""" # Could split into more a precise 0-5 state value, but it is unlikely to have any impact.
		return self.kart_collide.surface_properties().value
        
	def get_checkpoint_data(self):
		return {
			"lap_completion": self.race_mgr_player.lap_completion(),
			"race_completion": self.race_mgr_player.race_completion(),
			"race_completion_max": self.race_mgr_player.race_completion_max(),
			"checkpoint_id": self.race_mgr_player.checkpoint_id(),
			"current_key_checkpoint": self.race_mgr_player.current_kcp(),
			"max_key_checkpoint": self.race_mgr_player.max_kcp()
		}
	
	def get_respawn_point(self):
		return self.race_mgr_player.respawn()
	
	def get_driving_direction(self):
		"""
		DrivingDirection Enum:
		FORWARDS = 0
		BRAKING = 1
		WAITING_FOR_BACKWARDS = 2
		BACKWARDS = 3
		"""
		return self.kart_move.driving_direction() # 1 and 3 likely deserve negative rewards
	
	def get_wheelie_cooldown(self):
		if self.kart_move.is_bike: # sanity check in case of dumb programmers (me)
			return self.kart_move.wheelie_cooldown()
		print("ERROR: Requested wheelie cooldown on a kart")
		return 0
	
	def get_trick_cooldown(self):
		return self.kart_jump.cooldown()
	
	def get_airtime(self):
		return self.kart_move.airtime()

	def get_glitchy_timers(self):
		# Likely to never be useful to the ai unless forced to find ultras
		return {
			"horizontal_wall_glitch_timer": self.kart_state.hwg_timer(),
			"solid_oob_timer": self.kart_collide.solid_oob_timer(),
			"offroad_invincibility": self.kart_move.offroad_invincibility()
		}
	
	def get_item_count(self):
		# Thanks to vαbol∂ and Blounard for helping locate and pythonically access item information addresses
		return mkw_utils.chase_pointer(0x809c3618, [0x14, 0x00*0x248 + 0x90], 's32')
	
	def get_item_type(self):
		# Thanks to vαbol∂ and Blounard for helping locate and pythonically access item information addresses
		return mkw_utils.chase_pointer(0x809c3618, [0x14, 0x00*0x248 + 0x8C], 's32')