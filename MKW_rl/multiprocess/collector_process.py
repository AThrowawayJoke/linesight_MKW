"""
This file implements a single multithreaded worker that handles a Trackmania game instance and provides rollout results to the learner process.
"""

import importlib
import time
from itertools import chain, count, cycle
from pathlib import Path

import numpy as np
import torch
from torch import multiprocessing as mp

from config_files import config_copy
from MKW_rl import utilities
from MKW_rl.agents import iqn as iqn


def collector_process_fn(
    rollout_queue,
    uncompiled_shared_network,
    shared_network_lock,
    game_spawning_lock,
    shared_steps: mp.Value, # type: ignore # because it's fine at runtime so i wish to be rid of the warning
    base_dir: Path,
    save_dir: Path,
    tmi_port: int,
    process_number: int,
):
    from MKW_rl.map_loader import analyze_map_cycle, load_next_map_zone_centers
    from MKW_rl.MKW_interaction import game_manager_simple

    mkw = game_manager_simple.GameManager(
        game_spawning_lock=game_spawning_lock,
        running_speed=config_copy.running_speed,
        run_steps_per_action=config_copy.tm_engine_step_per_action,
        max_overall_duration_f=config_copy.cutoff_rollout_if_race_not_finished_within_duration_f,
        max_minirace_duration_f=config_copy.cutoff_rollout_if_no_vcp_passed_within_duration_f,
        tmi_port=tmi_port,
        process_number=process_number,
    )

    inference_network, uncompiled_inference_network = iqn.make_untrained_iqn_network(config_copy.use_jit, is_inference=True)
    try:
        inference_network.load_state_dict(torch.load(f=save_dir / "weights1.torch", weights_only=False))
    except Exception as e:
        print("Worker could not load weights, exception:", e)

    inferer = iqn.Inferer(inference_network, config_copy.iqn_k, config_copy.tau_epsilon_boltzmann)

    def update_network():
        # Update weights of the inference network
        with shared_network_lock:
            uncompiled_inference_network.load_state_dict(uncompiled_shared_network.state_dict())

    # ========================================================
    # Training loop
    # ========================================================
    inference_network.train()

    map_cycle_str = str(config_copy.map_cycle)
    set_maps_trained, set_maps_blind = analyze_map_cycle(config_copy.map_cycle)
    map_cycle_iter = cycle(chain(*config_copy.map_cycle))

    zone_centers_filename = None

    # ========================================================
    # Warmup pytorch and numba
    # ========================================================
    for _ in range(5):
        inferer.infer_network(
            np.random.randint(low=0, high=255, size=(1, config_copy.H_downsized, config_copy.W_downsized), dtype=np.uint8),
            np.random.rand(config_copy.float_input_dim).astype(np.float32),
        )
    # game_instance_manager.update_current_zone_idx(0, zone_centers, np.zeros(3))

    time_since_last_queue_push = time.perf_counter()
    last_loop_finished = False
    for loop_number in count(1):
        importlib.reload(config_copy)

        mkw.max_minirace_duration_f = config_copy.cutoff_rollout_if_no_vcp_passed_within_duration_f

        # ===============================================
        #   DID THE CYCLE CHANGE ?
        # ===============================================
        if str(config_copy.map_cycle) != map_cycle_str:
            map_cycle_str = str(config_copy.map_cycle)
            set_maps_trained, set_maps_blind = analyze_map_cycle(config_copy.map_cycle)
            map_cycle_iter = cycle(chain(*config_copy.map_cycle))

        # ===============================================
        #   GET NEXT MAP FROM CYCLE
        # ===============================================
        next_map_tuple = next(map_cycle_iter)
        if next_map_tuple[2] != zone_centers_filename:
            zone_centers = load_next_map_zone_centers(next_map_tuple[2], base_dir)
        map_name, map_path, zone_centers_filename, is_explo, fill_buffer = next_map_tuple
        map_status = "trained" if map_name in set_maps_trained else "blind"

        inferer.epsilon = utilities.from_exponential_schedule(config_copy.epsilon_schedule, shared_steps.value)
        inferer.epsilon_boltzmann = utilities.from_exponential_schedule(config_copy.epsilon_boltzmann_schedule, shared_steps.value)
        inferer.tau_epsilon_boltzmann = config_copy.tau_epsilon_boltzmann
        inferer.is_explo = is_explo

        # ===============================================
        #   PLAY ONE ROUND
        # ===============================================

        rollout_start_time = time.perf_counter()

        if inference_network.training and not is_explo:
            inference_network.eval()
        elif is_explo and not inference_network.training:
            inference_network.train()

        update_network()

        rollout_start_time = time.perf_counter()
        rollout_results, end_race_stats = mkw.rollout(
            exploration_policy=inferer.get_exploration_action,
            savestate_path=map_path,
            zone_centers=zone_centers,
            update_network=update_network,
            last_loop_finished=last_loop_finished,
        )
        rollout_end_time = time.perf_counter()
        rollout_duration = rollout_end_time - rollout_start_time
        rollout_results["worker_time_in_rollout_percentage"] = rollout_duration / (time.perf_counter() - time_since_last_queue_push)
        if end_race_stats["race_finished"]:
            last_loop_finished = True
        else:
            last_loop_finished = False
        time_since_last_queue_push = time.perf_counter()
        print("", flush=True)

        if not mkw.last_rollout_crashed:
            rollout_queue.put(
                (
                    rollout_results,
                    end_race_stats,
                    fill_buffer,
                    is_explo,
                    map_name,
                    map_status,
                    rollout_duration,
                    loop_number,
                )
            )
