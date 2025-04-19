from config_files import config_copy, user_config

import math
import os
import socket
import pickle
import struct
import subprocess
import time
from typing import Callable, Dict, List

import cv2
import numba
import numpy as np
import numpy.typing as npt
import psutil

import win32.lib.win32con as win32con
import win32com.client
import win32gui
import win32process

HOST = "127.0.0.1"
FRAME_WIDTH = 834
FRAME_HEIGHT = 456

class GameManager:
    def __init__(
        self,
        game_spawning_lock,
        running_speed=1,
        run_steps_per_action=10,
        max_overall_duration_ms=2000,
        max_minirace_duration_ms=2000,
        tmi_port=None,
    ):
        # Create TMInterface we will be using to interact with the game client
        self.iface = None
        self.sock = None
        self.latest_tm_engine_speed_requested = 1
        self.running_speed = running_speed
        self.run_steps_per_action = run_steps_per_action
        self.max_overall_duration_ms = max_overall_duration_ms
        self.max_minirace_duration_ms = max_minirace_duration_ms
        self.timeout_has_been_set = False
        self.msgtype_response_to_wakeup_TMI = None
        self.latest_savestate_path_requested = -2
        self.last_rollout_crashed = False
        self.last_game_reboot = time.perf_counter()
        self.UI_disabled = False
        self.tmi_port = tmi_port
        self.dolphin_process_id = None
        self.dolphin_window_id = None
        self.start_states = {} # oh hey I might want to use this for starting later on in the track
        self.game_spawning_lock = game_spawning_lock
        self.game_activated = False
    
    def get_window_id(self):
        assert self.dolphin_process_id is not None

        def get_hwnds_for_pid(pid):
            def callback(hwnd, hwnds):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

                if found_pid == pid:
                    hwnds.append(hwnd)
                return True

            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            return hwnds

        while True:
            for hwnd in get_hwnds_for_pid(self.dolphin_process_id):
                if "Dolphin" in win32gui.GetWindowText(hwnd):
                    self.dolphin_window_id = hwnd
                    return
                # else:
                #     raise Exception("Could not find TmForever window id.")

    def register(self):
        timeout = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # signal.signal(signal.SIGINT, self.signal_handler) # Handle close game signal
        # https://stackoverflow.com/questions/45864828/msg-waitall-combined-with-so-rcvtimeo
        # https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
        if timeout is not None:
            if config_copy.is_linux:  # https://stackoverflow.com/questions/46477448/python-setsockopt-what-is-worng
                timeout_pack = struct.pack("ll", timeout, 0)
            else:
                timeout_pack = struct.pack("q", timeout * 1000)
            # Set the maximum amount for time the socket will wait for a response and/or attempt to send data.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout_pack)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, timeout_pack)
        # Ensure packets are sent immediately instead of waiting for larger batches to be created
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((HOST, self.tmi_port))
        self.registered = True
        print("Connected")

    # Launch program and return pids
    def launch_game(self):
        self.dolphin_process_id = None

        if config_copy.is_linux:
            """self.game_spawning_lock.acquire()
            pid_before = self.get_tm_pids()
            os.system(str(user_config.linux_launch_game_path) + " " + str(self.tmi_port))
            while True:
                pid_after = self.get_tm_pids()
                tmi_pid_candidates = set(pid_after) - set(pid_before)
                if len(tmi_pid_candidates) > 0:
                    assert len(tmi_pid_candidates) == 1
                    break
            self.tm_process_id = list(tmi_pid_candidates)[0]"""
            pass
        else:
            # See Dolphin Command Line Usage for more information (https://github.com/dolphin-emu/dolphin)
            launch_string = (
                'powershell -executionPolicy bypass -command "& {'
                f" $process = start-process -FilePath '{user_config.windows_Dolphinexe_path}'" # Launch .exe file
                " -PassThru -ArgumentList " # Assign arguments for .exe
                f'\'--video_backend="{user_config.video_backend}" --script game_instance_hook.py --no-python-subinterpreters --exec="{user_config.game_path}"\';'
                ' echo exit $process.id}"' # push process_id to stdout to read later
            )

            
            self.dolphin_process_id = int(subprocess.check_output(launch_string).decode().split("\r\n")[1]) # locate the pid from the program
            # We do not need the parent of returned process id for this fork
            """while self.dolphin_process_id is None:
                dolphin_processes = list(
                    filter(
                        lambda s: s.startswith("Dolphin"), # confirm this is a Dolphin process
                        subprocess.check_output("wmic process get Caption,ParentProcessId,ProcessId").decode().split("\r\n"),
                    )
                ) # create a list of Dolphin processes by filtering out unmatching ones and checking their output
                for process in dolphin_processes:
                    name, parent_id, process_id = process.split() # extract information from process
                    parent_id = int(parent_id)
                    process_id = int(process_id)
                    if parent_id == dolphin_process_id: # confirm we have our Dolphin process and assign it
                        self.dolphin_process_id = process_id
                        break"""

        print(f"Found Dolphin process id: {self.dolphin_process_id=}")
        self.last_game_reboot = time.perf_counter() # set counter to know how old the process is
        self.latest_map_path_requested = -1
        self.msgtype_response_to_wakeup_TMI = None
        while not self.is_game_running(): # wait for the program to launch fully
            time.sleep(0)

        self.get_window_id() # locate window ID for the process

    def is_game_running(self):
        return (self.dolphin_process_id is not None) and (self.dolphin_process_id in (p.pid for p in psutil.process_iter()))

    def is_dolphin_process(self, process: psutil.Process) -> bool:
        try:
            return "Dolphin" in process.name()
        except psutil.NoSuchProcess:
            return False

    def get_dolphin_pids(self) -> List[int]:
        return [process.pid for process in psutil.process_iter() if self.is_dolphin_process(process)]

    def close_game(self):
        self.timeout_has_been_set = False
        self.game_activated = False
        assert self.dolphin_process_id is not None
        if config_copy.is_linux:
            os.system("kill -9 " + str(self.dolphin_process_id))
        else:
            os.system(f"taskkill /PID {self.dolphin_process_id} /f")
        while self.is_game_running(): # wait for process to fully close
            time.sleep(0)

    def ensure_game_launched(self):
        if not self.is_game_running():
            print("Game not found. Starting Dolphin.")
            self.launch_game()

    """# Using Felk fork.
    async def grab_screen(self):
        # (width, height, data)
        large_image = await event.framedrawn()
        print(large_image.shape)
        # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
        input_size = 640
        output_size = 128
        bin_size = input_size // output_size # modular ratio of input to output
        small_image = large_image.reshape((1, output_size, bin_size, output_size, bin_size)).max(4).max(2)
        return small_image"""

    """def set_inputs(self, action_idx: int, rollout_results: Dict):
        if (
            len(rollout_results["actions"]) == 0 or rollout_results["actions"][-1] != action_idx
        ):  # Small performance trick, don't update input_state if it doesn't need to be updated
            # TODO: Adjust for dolphin
            self.iface.set_input_state(**config_copy.inputs[action_idx]) # inputs from inputs_list.py"""

    """def select_map_savestate(self, savestate_path: str, zone_centers: npt.NDArray):
    # TODO: Convert to loading a specific savestate of chosen track one frame before countdown
    # This method also allows different vehicle combinations by proxy.
        self.latest_savestate_path_requested = savestate_path
        if user_config.is_linux:
            savestate_path = savestate_path.replace("\\", "/")
        else:
            savestate_path = savestate_path.replace("/", "\\")
    # TODO: Include a dictionary of track savestates somewhere
        savestate.load_from_file(savestate_path)
        self.UI_disabled = False
        (
            self.next_real_checkpoint_positions,
            self.max_allowable_distance_to_real_checkpoint,
        ) = map_loader.sync_virtual_and_real_checkpoints(zone_centers, savestate_path)"""

    def rollout(self, exploration_policy: Callable, savestate_path: str, update_network: Callable):
        """
        exploration_policy: Function that returns ratio of exploration vs exploitation runs
        savestate_path: file path to current track to run
        update_network: function to send network information to update itself with
        """

        self.ensure_game_launched()
        if time.perf_counter() - self.last_game_reboot > config_copy.game_reboot_interval: # stale instance of game
            self.close_game()
            self.sock = None
            self.launch_game()

        end_race_stats = {
            "cp_time_ms": [0],
        }

        instrumentation__answer_normal_step = 0
        instrumentation__answer_action_step = 0
        instrumentation__between_run_steps = 0
        instrumentation__grab_frame = 0
        instrumentation__request_inputs_and_speed = 0
        instrumentation__exploration_policy = 0
        instrumentation__convert_frame = 0
        instrumentation__grab_floats = 0

        # TODO: Determine what values need to be saved to the ReplayBuffer
        rollout_results = {
            "current_checkpoint_id": [],
            "frames": [],
            "input_w": [], # Whether or not w is pressed
            "actions": [], # list of actions
            "action_was_greedy": [], # whether action is greedy as defined by the epxloration policy
            "q_values": [],
            "race_completion": [],
            "state_float": [], # specifics about game data we want ai to know
            "furthest_zone_idx": 0,
        }

        last_progress_improvement_ms = 0

        if (self.sock is None) or (not self.registered): # Game was not connected to the program
            assert self.msgtype_response_to_wakeup_TMI is None
            print("Initialize connection to TMInterface ")
            # self.iface = TMInterface(self.tmi_port) # reset the interface

            connection_attempts_start_time = time.perf_counter()
            last_connection_error_message_time = time.perf_counter()
            while True:
                try:
                    self.register(config_copy.tmi_protection_timeout_s) # connect to the interface
                    break
                except ConnectionRefusedError as e:
                    current_time = time.perf_counter()
                    if current_time - last_connection_error_message_time > 1:
                        print(f"Connection to TMInterface unsuccessful for {current_time - connection_attempts_start_time:.1f}s")
                        last_connection_error_message_time = current_time
        """else:
            assert self.msgtype_response_to_wakeup_TMI is not None or self.last_rollout_crashed # Game is running and connected

            self.request_speed(self.running_speed) # FPS?
            if self.msgtype_response_to_wakeup_TMI is not None:
                self.iface._respond_to_call(self.msgtype_response_to_wakeup_TMI)
                self.msgtype_response_to_wakeup_TMI = None"""

        self.last_rollout_crashed = False

        _time = -3000 # track how long this rollout has been going
        current_zone_idx = config_copy.n_zone_centers_extrapolate_before_start_of_map

        # Insert values for the start of a race
        computed_action = None
        give_up_signal_has_been_sent = False
        this_rollout_has_seen_t_negative = False
        this_rollout_is_finished = False
        n_th_action_we_compute = 0
        compute_action_asap = False
        compute_action_asap_floats = False
        frame_expected = False
        map_change_requested_time = math.inf

        last_known_simulation_state = None
        pc = 0 # performance counter
        pc5 = 0
        floats = None

        distance_since_track_begin = 0.999 # Beginning lap completion percentage is usually about 0.999, depending on the track
        sim_state_car_gear_and_wheels = None

        sim_state = None

        while not this_rollout_is_finished:
            """
            This loop needs to perform these essential functions:
            1. Load race savestate (enforce mini-races and race finishes)
            2. Read game state (floats and frame)
            3. Send data to exploration policy
            4. Send inputs received from exploration policy to the game
            5. update the network
            """
            if self.latest_map_path_requested != savestate_path:
                # We have to load the savestate we want
                if computed_action != None:
                    self.sock.sendall(pickle.dumps([False, False, computed_action, savestate_path]))
                else:
                    self.sock.sendall(pickle.dumps([False, False, computed_action, savestate_path]))
                self.latest_map_path_requested = savestate_path # this seems backwards... TODO
                continue

            if computed_action != None:
                self.sock.sendall(pickle.dumps([True, True, computed_action, None]))
            else:
                self.sock.sendall(pickle.dumps([True, True, None, None]))
            # The following line brought to you by literal hours of trying to figure things out only to realize I just needed two functions that I could've just copied from the original code
            frame_data = np.frombuffer(self.sock.recv(FRAME_WIDTH * FRAME_HEIGHT * 3, socket.MSG_WAITALL), dtype = np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))
            # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
            resized_frame = frame_data[::6,::6]
            """if frame_counter % 240 == 0:
                cv2.imshow("Greyscale", cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY))
                cv2.waitKey(0)""" # Image is collected properly, next step is to save to file for display.
            resized_frame = np.expand_dims(cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY), 0) # took me like 80 minutes to get to the solution that was already present in the original code
            # frame is a numpy array of shape (1, H, W) and dtype np.uint8

            rollout_results["frames"].append(resized_frame)
            game_data = pickle.loads(self.sock.recv(8192))



            if compute_action_asap_floats:
                pc2 = time.perf_counter_ns()

                previous_actions = [
                    # Get inputs from k for every k that we have not processed yet
                    config_copy.inputs[rollout_results["actions"][k] if k >= 0 else config_copy.action_forward_idx]
                    for k in range(
                        len(rollout_results["actions"]) - config_copy.n_prev_actions_in_inputs, len(rollout_results["actions"])
                    )
                ]


                # unfinished
                floats = np.hstack(
                    0,
                    np.array(
                        [
                            previous_action[input_key]
                            for previous_action in previous_actions
                            for input_key in [
                                "A", 
                                "B", 
                                "X", 
                                "Y", 
                                "Z", 
                                "Start", 
                                "Up", 
                                "Down", 
                                "Left", 
                                "Right", 
                                "L", 
                                "R", 
                                "StickX", 
                                "StickY", 
                                "CStickX", 
                                "CStickY", 
                                "TriggerLeft", 
                                "TriggerRight"
                            ]
                        ],
                        game_data
                    )
                ).astype(np.float32)

            if _time > 0 and this_rollout_has_seen_t_negative:
                if _time % 50 == 0:
                    instrumentation__between_run_steps += time.perf_counter_ns() - pc # time the run step took
            pc = time.perf_counter_ns()

            # ============================
            # BEGIN ON RUN STEP
            # ============================


            (
                action_idx,
                action_was_greedy,
                q_value,
                q_values,
            ) = exploration_policy(rollout_results["frames"][-1], floats) # TODO: consider replacing list index with available variable resized_frame

            self.desired_inputs = config_copy.inputs[action_idx]  # determine next input
            rollout_results["meters_advanced_along_centerline"].append(game_data[2]["race_completion_max"] - 0.998) # Negate starting lap completion percentage
            rollout_results["input_w"].append(config_copy.inputs[action_idx]["A"])
            rollout_results["actions"].append(action_idx)
            rollout_results["action_was_greedy"].append(action_was_greedy)
            rollout_results["q_values"].append(q_values)
            rollout_results["state_float"].append(floats)

            n_th_action_we_compute += 1

            if _time % (10 * self.run_steps_per_action * config_copy.update_inference_network_every_n_actions) == 0:
                update_network()

            if not self.timeout_has_been_set:
                # reset the ai for doing bad things for too long?
                self.timeout_has_been_set = True
            
            if _time == 0 and (savestate_path != self.latest_map_path_requested):
                map_change_requested_time = _time
                give_up_signal_has_been_sent = True

            exploration_policy(rollout_results, end_race_stats)

