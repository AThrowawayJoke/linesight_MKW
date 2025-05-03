import numpy as np

float_inputs_mean = np.array(
    [
        70,  # temporal_mini_race_duration_actions / 2
        #######
        0.8,
        0.2,
        0.3,
        0.3,
        0.8,
        0.2,
        0.3,
        0.3,
        0.8,
        0.2,
        0.3,
        0.3,
        0.8,
        0.2,
        0.3,
        0.3,
        0.8,
        0.2,
        0.3,
        0.3,
        # Previous action
        0.1,
        0.1,
        0.1,
        0.1,
        0.9,
        0.9,
        0.9,
        0.9,
        0.02,
        0.02,
        0.02,
        0.02,
        0.3,
        2.5,
        7000,
        0.1,  # Car gear and wheels
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,  # Wheel contact material types
        0,
        0,
        0,  # Angular velocity
        #######
        0,
        0,
        55,
        0,
        1,
        0,
        700,  # margin_to_announce_finish_meters
        0,  # is_freewheeling
    ]
)

float_inputs_std = np.array(
    [
        70,  # temporal_mini_race_duration_actions / 2
        #######
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,  # Previous action
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.06,
        0.06,
        0.06,
        0.06,
        1,
        2,
        3000,
        10,  # Car gear and wheels
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,
        0.5,  # Wheel contact material types
        0.5,
        1,
        0.5,  # Angular velocity
        #######
        5,
        5,
        20,
        0.5,
        0.5,
        0.5,
        350,  # margin_to_announce_finish_meters / 2
        1,  # is_freewheeling
    ]
)
