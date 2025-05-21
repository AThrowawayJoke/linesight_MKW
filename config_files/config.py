"""
This file contains a run's configuration.
It is expected that this file contains all relevant information about a run.

Two files named "config.py" and "config_copy.py" coexist in the same folder.

At the beginning of training, parameters are copied from config.py to config_copy.py
During training, config_copy.py will be reloaded at regular time intervals.
config_copy.py is NOT tracked in git, as it is essentially a temporary file.

Training parameters modifications made during training in config_copy.py will be applied on the fly
without losing the existing content of the replay buffer.

The content of config.py may be modified after starting a run: it will have no effect on the ongoing run.
This setup provides the possibility to:
1) Modify training parameters on the fly
2) Continue to code, use git, and modify config.py without impacting an ongoing run.

This file is preconfigured with sensible hyperparameters for the map ESL-Hockolicious, assuming the user
has a computer with 16GB RAM.
"""
from itertools import repeat

from config_files.inputs_list import *
from config_files.state_normalization import *
from config_files.user_config import *

W_downsized = 153
H_downsized = 114

run_name = "LC_mushroom_retry"
running_speed = 80
restart_race_command = "restart_race"

LC_punish_line = 44600
LC_punish_rate = 5
LC_mushroom_point = 4.68

tm_engine_step_per_action = 2
f_per_action = tm_engine_step_per_action
game_running_fps = 30
n_zone_centers_in_inputs = 40
one_every_n_zone_centers_in_inputs = 5
n_zone_centers_extrapolate_after_end_of_map = 500
n_zone_centers_extrapolate_before_start_of_map = 20

n_prev_actions_in_inputs = 5

n_contact_material_physics_behavior_types = 4  # See contact_materials.py
cutoff_rollout_if_race_not_finished_within_duration_f = game_running_fps * 10_800 # 6m at 30fps
cutoff_rollout_if_no_vcp_passed_within_duration_f = game_running_fps * 4 # 4s

temporal_mini_race_duration_f = game_running_fps * 7
temporal_mini_race_duration_actions = temporal_mini_race_duration_f // f_per_action
oversample_long_term_steps = 40
oversample_maximum_term_steps = 5
min_horizon_to_update_priority_actions = temporal_mini_race_duration_actions - 40
# If mini_race_time == mini_race_duration this is the end of the minirace
margin_to_announce_finish_meters = 700

global_schedule_speed = 1.5

constant_reward_per_action = -2 / (7 * (game_running_fps / f_per_action))

epsilon_schedule = [
    (0, 1),
    (50_000, 1),
    (300_000, 0.1),
    (3_000_000 * global_schedule_speed, 0.03),
]
epsilon_boltzmann_schedule = [
    (0, 0.15),
    (3_000_000 * global_schedule_speed, 0.03),
]
tau_epsilon_boltzmann = 0.01
discard_non_greedy_actions_in_nsteps = True
buffer_test_ratio = 0.05

engineered_speedslide_reward_schedule = [
    (0, 0),
]
engineered_neoslide_reward_schedule = [
    (0, 0),
]
engineered_kamikaze_reward_schedule = [
    (0, 0),
]

"""(0, 1 * -constant_reward_per_action), # 2 per action
    (50_000, 1 * -constant_reward_per_action),
    (500_000 * global_schedule_speed, 0.8 * -constant_reward_per_action),
    (3_000_000 * global_schedule_speed, 0.4 * -constant_reward_per_action),
    (5_000_000 * global_schedule_speed, 0 * -constant_reward_per_action),"""
engineered_close_to_vcp_reward_schedule = [
    (0, 0)
]
# Reward A.I. for accelerating
engineered_holding_A_reward_schedule = [
    (0, 2),
    (50_000, 2),
    (300_000 * global_schedule_speed, 1),
    (3_000_000 * global_schedule_speed, 0),
]
# Punish A.I. for using an item as a ratio multiplier to progress made during boost
engineered_item_usage_reward_schedule = [
    (0, 5),
    (50_000, 5),
    (300_000 * global_schedule_speed, 5),
    (3_000_000 * global_schedule_speed, 4),
]

engineered_supergrinding_reward_schedule = [
    (0, 0),
]

engineered_start_boost_charge_reward_schedule = [
    (0, 0),
]

"""
it is recommended to work with standardized values for the inputs of the neural network.

The same recommendation holds for the output of the neural network.

Since the neural network outputs returns, you want your returns to be somewhat normalized.
What does it mean?

It means that when the agent plays well in a favorable scenario, returns should be somewhere around 2.
If the agent plays bad in an unfavorable scenario, returns should be somewhere around -2.
If the agent plays neither good neither bad, returns should be around 0.

For Trackmania, we could say that
"playing well" is being able to achieve 300km/h on average.  We can calculate the theoretical returns obtained by the agent and make sure it's around 2.
"playing bad" is achieving 100km/h on average. We can calculate the theoretical returns obtained by the agent and make sure it's around -2.

This is where these magic numbers come from:
constant_reward_per_ms = -6 / 5000
reward_per_m_advanced_along_centerline = 5 / 500
"""

n_steps = 3

# -4 / time_per_lap * lap_count * actions_per_second
expected_lap_duration_s = 25

expected_lap_duration_per_action = expected_lap_duration_s * (game_running_fps / f_per_action) # at 60 fps
average_lap_increment_per_action = 1 / expected_lap_duration_per_action
total_second_increment_expected = 3 / (expected_lap_duration_s * 3 / 7)

# added_race_completion * 2
# expected_lap_count * 3 / 7 # how many 7-second increments per lap
# total_distance_traveled = 3 
# total_distance_traveled / (expected_lap_duration_s * 3 / 7) = distance_we_should_progress in 7 seconds
# distance_we_should_progress_ratio (4)

reward_per_m_advanced_along_centerline = 4 / total_second_increment_expected

# Reward functions for standard progression along the track
final_speed_reward_as_if_duration_s = 0.00002 # times speed (80) times reward_per_m (1000) = 
final_speed_reward_per_f_per_s = reward_per_m_advanced_along_centerline * final_speed_reward_as_if_duration_s


required_progress_per_cutoff_rollout = 0.002 # 5/1000ths of a lap
required_progress_ratio = expected_lap_duration_per_action / cutoff_rollout_if_no_vcp_passed_within_duration_f # 1800 / 180 = 10 frames?
lap_completion_required_per_expected_lap_completion = required_progress_ratio * required_progress_per_cutoff_rollout # Ratio of how much of the lap we require to what we should have completed per no-progress cutoff period

# 2000 per lap, 1800 frames per lap, ~1.1 reward per frame
button_A_held_reward_per_f = reward_per_m_advanced_along_centerline / expected_lap_duration_per_action
button_A_held_reward_per_s = button_A_held_reward_per_f * game_running_fps
# Expected to spend ~30s per lap on short tracks, ~45s on longer tracks.
# Use ratio of m advanced to determine reward
# Unknown if adjusting for start boost would be good

# Mushroom boost punishments. Mushrooms last 1.5s, and give roughly +30-40 speed

# Numper of game_data points + 7 (number of input buttons in 1 input) * number of previous actions + 3 (3d point) * n zone centers
float_input_dim = 42 + 7 * n_prev_actions_in_inputs + 3 * n_zone_centers_in_inputs

float_hidden_dim = 256
conv_head_output_dim = 5280
dense_hidden_dimension = 1024
iqn_embedding_dimension = 64
iqn_n = 8  # must be an even number because we sample tau symmetrically around 0.5
iqn_k = 32  # must be an even number because we sample tau symmetrically around 0.5
iqn_kappa = 5e-3
use_ddqn = False

prio_alpha = np.float32(0)  # Rainbow-IQN paper: 0.2, Rainbow paper: 0.5, PER paper 0.6
prio_epsilon = np.float32(2e-3)  # Defaults to 10^-6 in stable-baselines
prio_beta = np.float32(1)

# State-action pair processed in action exploration will be discarded after randomly selected this amount of times
number_times_single_memory_is_used_before_discard = 32  # 32 // 4

# Schedule how many state-action pairs we save in memory at specific sections of training
memory_size_schedule = [
    (0, (50_000, 20_000)),
    (500_000 * global_schedule_speed, (125_000, 50_000)),
    (1_000_000 * global_schedule_speed, (400_000, 125_000)),
    (2_000_000 * global_schedule_speed, (1_100_000, 250_000)),
]
lr_schedule = [
    (0, 1e-3),
    (3_000_000 * global_schedule_speed, 5e-5),
    (12_000_000 * global_schedule_speed, 5e-5),
    (15_000_000 * global_schedule_speed, 1e-5),
]
tensorboard_suffix_schedule = [
    (0, ""),
    (6_000_000 * global_schedule_speed, "_2"),
    (15_000_000 * global_schedule_speed, "_3"),
    (30_000_000 * global_schedule_speed, "_4"),
    (45_000_000 * global_schedule_speed, "_5"),
    (80_000_000 * global_schedule_speed, "_6"),
    (150_000_000 * global_schedule_speed, "_7"),
]
gamma_schedule = [
    (0, 0.999),
    (1_500_000, 0.999),
    (2_500_000, 1),
]

batch_size = 512
weight_decay_lr_ratio = 1 / 50
adam_epsilon = 1e-4
adam_beta1 = 0.9
adam_beta2 = 0.999

single_reset_flag = 0
reset_every_n_frames_generated = 400_000_00000000
additional_transition_after_reset = 1_600_000
last_layer_reset_factor = 0.8  # 0 : full reset, 1 : nothing happens
overall_reset_mul_factor = 0.01  # 0 : nothing happens ; 1 : full reset

clip_grad_value = 1000
clip_grad_norm = 30

# Number of state-action pairs we train before updating the Target Network as defined by DQN.
number_memories_trained_on_between_target_network_updates = 2048
soft_update_tau = 0.02

# Helper values
distance_between_checkpoints = 300
# Old values were 0.5 dbc and 90 rw. I have set the road_width to roughly match those values' ratios (90/0.5 = 180, 20000/300 = 66.67) taking 'closer to 24' into account (24/0.5 = 48)
road_width = 30000  ## a little bit of margin, could be closer to 24 probably ? Don't take risks there are curvy roads
max_allowable_distance_to_virtual_checkpoint = np.sqrt((distance_between_checkpoints / 2) ** 2 + (road_width / 2) ** 2)

# Restart intervals in case of lost connection or game crash
timeout_during_run_ms = 10_100
timeout_between_runs_ms = 600_000_000
tmi_protection_timeout_s = 500
game_reboot_interval = 3600 * 8  # In seconds

# Do not save runs until after we start getting roughly human-level results (i.e. prevent saving 1000s of extra bad runs)
frames_before_save_best_runs = 3_000_000

plot_race_time_left_curves = False
n_transitions_to_plot_in_distribution_curves = 1000
make_highest_prio_figures = False
apply_randomcrop_augmentation = False
n_pixels_to_crop_on_each_side = 2

max_rollout_queue_size = 1

use_jit = True

# gpu_collectors_count is the number of Dolphin instances that will be launched in parallel.
# It is recommended that users adjust this number depending on the performance of their machine.
# We recommend trying different values and finding the one that maximises the number of batches done per unit of time.
# Note that each additional instance requires a separate folder containing a full Dolphin installation, and should be named sequentially. (Dolphin's game save files cannot be shared between instances)
# For instance, if the original install is called 'dolphin_folder', installations 2 and 3 should be named 'dolphin_folder2' and 'dolphin_folder3'.
gpu_collectors_count = 3

# Every n batches, each collection process updates it's network to match the current Online Network as defined by DQN
send_shared_network_every_n_batches = 10
update_inference_network_every_n_actions = 20

target_self_loss_clamp_ratio = 4


shaped_reward_dist_to_cur_vcp = -0.0005
shaped_reward_min_dist_to_cur_vcp = 2
shaped_reward_max_dist_to_cur_vcp = 25
engineered_reward_min_dist_to_cur_vcp = 900 # max reward
engineered_reward_max_dist_to_cur_vcp = 5000 # minimum reward
shaped_reward_point_to_vcp_ahead = 0

threshold_to_save_all_runs_ms = -1

deck_height = -np.inf
game_camera_number = 2

sync_virtual_and_real_checkpoints = True

""" 
============================================      MAP CYCLE     =======================================================

In this section we define the map cycle.

It is a list of iterators, each iterator must return tuples with the following information:
    - short map name        (string):     for logging purposes
    - map path              (string):     to automatically load the map in game. 
                                          This is the same map name as the "map" command in the TMInterface console.
    - reference line path   (string):     where to find the reference line for this map
    - is_explo              (boolean):    whether the policy when running on this map should be exploratory
    - fill_buffer           (boolean):    whether the memories generated during this run should be placed in the buffer 

The map cycle may seem complex at first glance, but it provides a large amount of flexibility:
    - can train on some maps, test blindly on others
    - can train more on some maps, less on others
    - can define multiple reference lines for a given map
    - etc...

The example below defines a simple cycle where the agent alternates between four exploratory runs on map5, and one 
evaluation run on the same map.

map_cycle = [
    repeat(("map5", '"My Challenges/Map5.Challenge.Gbx"', "map5_0.5m_cl.npy", True, True), 4),
    repeat(("map5", '"My Challenges/Map5.Challenge.Gbx"', "map5_0.5m_cl.npy", False, True), 1),
]
"""

# TODO: Add expected race times to balance return (goal is ranging from 2 for good run to -2 for bad, 0 being average (i.e expected) time)

nadeo_maps_to_train_and_test = [
    "A01-Race",
    # "A02-Race",
    "A03-Race",
    # "A04-Acrobatic",
    "A05-Race",
    # "A06-Obstacle",
    "A07-Race",
    # "A08-Endurance",
    # "A09-Race",
    # "A10-Acrobatic",
    "A11-Race",
    # "A12-Speed",
    # "A13-Race",
    "A14-Race",
    "A15-Speed",
    "B01-Race",
    "B02-Race",
    "B03-Race",
    # "B04-Acrobatic",
    "B05-Race",
    # "B06-Obstacle",
    # "B07-Race",
    # "B08-Endurance",
    # "B09-Acrobatic",
    "B10-Speed",
    # "B11-Race",
    # "B12-Race",
    # "B13-Obstacle",
    "B14-Speed",
    # "B15-Race",
]

map_cycle = []
# for map_name in nadeo_maps_to_train_and_test:
#   short_map_name = map_name[0:3]
#   map_cycle.append(repeat((short_map_name, f'"Official Maps\{map_name}.Challenge.Gbx"', f"{map_name}_0.5m_cl2.npy", True, True), 4))
#   map_cycle.append(repeat((short_map_name, f'"Official Maps\{map_name}.Challenge.Gbx"', f"{map_name}_0.5m_cl2.npy", False, True), 1))


map_cycle += [
    # repeat(("rGV2_auto", "linesight_savestates\\rGV2_auto_hitbox_charge2.sav", "rGV2.npy", True, True), 4),
    # repeat(("rGV2_auto", "linesight_savestates\\rGV2_auto_hitbox_charge2.sav", "rGV2.npy", False, True), 1),
    # repeat(("rGV2", "linesight_savestates\\rGV2_F_FR_hitbox.sav", "rGV2.npy", True, True), 4),
    # repeat(("rGV2", "linesight_savestates\\rGV2_F_FR_hitbox.sav", "rGV2.npy", False, True), 1),
    # repeat(("rMC3", "linesight_savestates\\rMC3_D_MB_hitbox.sav", "rMC3.npy", True, True), 4),
    # repeat(("rMC3", "linesight_savestates\\rMC3_D_MB_hitbox.sav", "rMC3.npy", False, True), 1),
    # repeat(("rMC3", "__slot__2", "rMC3.npy", True, True), 4),
    # repeat(("rMC3", "__slot__2", "rMC3.npy", False, True), 1),
    # repeat(("MG", "linesight_savestates\\MG_F_SS.sav", "MG.npy", True, True), 4), # load from savestate slot instead of file?
    # repeat(("MG", "linesight_savestates\\MG_F_SS.sav", "MG.npy", False, True), 1),
    repeat(("LC", "linesight_savestates\\LC_F_Sp.sav", "LC.npy", True, True), 4),
    repeat(("LC", "linesight_savestates\\LC_F_Sp.sav", "LC.npy", False, True), 1),
]
