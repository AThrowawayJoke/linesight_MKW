from multiprocessing import process
from config_files import config_copy, user_config

import math
import os
from multiprocessing.connection import Client
import subprocess
import time
from typing import Callable, Dict, List
import flatdict

from MKW_rl.MKW_interaction.MKW_data_translate import *
from config_files.inputs_list import GCInputs

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
FRAME_WIDTH = 611
FRAME_HEIGHT = 456

class GameManager:
    def __init__(
        self,
        game_spawning_lock,
        running_speed=1,
        run_steps_per_action=10,
        max_overall_duration_f=2000,
        max_minirace_duration_f=2000,
        tmi_port=None,
        process_number=None
    ):
        # Create TMInterface we will be using to interact with the game client
        self.iface = None
        self.sock = None
        self.latest_tm_engine_speed_requested = 1
        self.running_speed = running_speed
        self.run_steps_per_action = run_steps_per_action
        self.max_overall_duration_f = max_overall_duration_f
        self.max_minirace_duration_f = max_minirace_duration_f
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
        self.process_number = process_number
    
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

    def register(self, timeout=None):
        # https://stackoverflow.com/questions/6920858/interprocess-communication-in-python
        self.sock = Client((HOST, self.tmi_port))
        """# signal.signal(signal.SIGINT, self.signal_handler) # Handle close game signal
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
        self.sock.connect((HOST, self.tmi_port))"""
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
            # print(user_config.base_tmi_port, " This is a test ", config_copy.trackmania_base_path) # Issue: user_config was not reflecting changes made. Solution: "pip uninstall linesight". A version of linesight in another location was taking priority
            # See Dolphin Command Line Usage for more information (https://github.com/dolphin-emu/dolphin) (https://wiki.dolphin-emu.org/index.php?title=GameINI)
            dolphin_process_number = ""
            if self.process_number >= 1:
                dolphin_process_number = self.process_number + 1
            
            # print("Dolphin process number assigned as:", dolphin_process_number, "Derived from received process number of", self.process_number)
            launch_string = (
                'powershell -executionPolicy bypass -command "& {'
                f" $process = start-process -FilePath '{config_copy.dolphin_base_path}{dolphin_process_number}\\{config_copy.windows_dolphinexe_filename}'" # Launch .exe file
                " -PassThru -ArgumentList " # Assign arguments for .exe
                f'\'--video_backend="{config_copy.video_backend}" --config=Dolphin.Core.EmulationSpeed={config_copy.game_speed} --script MKW_rl\\MKW_interaction\\game_instance_hook.py --no-python-subinterpreters --exec="{config_copy.game_path}"\';'
                ' echo exit $process.id}"' # push process_id to stdout to read later
            )
            # print(launch_string)
            
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
            "action_was_greedy": [], # whether action is greedy as defined by the exploration policy
            "q_values": [],
            "race_completion": [],
            "state_float": [], # specifics about game data we want ai to know
            "furthest_zone_idx": 0,
        }

        last_progress_improvement_f = 0

        if (self.sock is None) or (not self.registered): # Game was not connected to the program
            assert self.msgtype_response_to_wakeup_TMI is None
            print("Initialize connection to Dolphin from game_manager")
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
                        print(f"Connection to Dolphin unsuccessful for {current_time - connection_attempts_start_time:.1f}s")
                        last_connection_error_message_time = current_time
        """else:
            assert self.msgtype_response_to_wakeup_TMI is not None or self.last_rollout_crashed # Game is running and connected

            self.request_speed(self.running_speed) # FPS?
            if self.msgtype_response_to_wakeup_TMI is not None:
                self.iface._respond_to_call(self.msgtype_response_to_wakeup_TMI)
                self.msgtype_response_to_wakeup_TMI = None"""

        self.last_rollout_crashed = False

        frames_processed = 0 # track how long this rollout has been going
        current_zone_idx = config_copy.n_zone_centers_extrapolate_before_start_of_map

        # Insert values for the start of a race
        computed_action = None
        give_up_signal_has_been_sent = False
        this_rollout_has_seen_t_negative = False
        this_rollout_is_finished = False
        n_th_action_we_compute = 0
        compute_action_asap = True
        compute_action_asap_floats = True
        frame_expected = False
        map_change_requested_time = math.inf

        last_known_simulation_state = None
        pc = 0 # performance counter
        pc5 = 0
        floats = None

        distance_since_track_begin = 0.999 # Beginning lap completion percentage is usually about 0.999, depending on the track
        sim_state_car_gear_and_wheels = None

        game_data = None

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
                self.sock.send([False, False, computed_action, savestate_path])
                self.latest_map_path_requested = savestate_path # this seems backwards... TODO
                continue

            if (frames_processed % self.run_steps_per_action != 0):
                self.sock.send([False, False, computed_action, None])
                compute_action_asap_floats = True
                continue

            self.sock.send([True, True, computed_action, None])

            # print("Now waiting for frame data.")
            # The following line brought to you by literal hours of trying to figure things out only to realize I just needed two functions that I could've just copied from the original code
            frame_data = np.frombuffer(self.sock.recv_bytes(FRAME_WIDTH * FRAME_HEIGHT * 3), dtype = np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))
            frames_processed += 1
            # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
            resized_frame = frame_data[::6,::6]
            """if frame_counter % 240 == 0:
                cv2.imshow("Greyscale", cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY))
                cv2.waitKey(0)""" # Image is collected properly, next step is to save to file for display.
            resized_frame = np.expand_dims(cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY), 0) # took me like 80 minutes to get to the solution that was already present in the original code
            # frame is a numpy array of shape (1, H, W) and dtype np.uint8

            rollout_results["frames"].append(resized_frame)
            game_data = self.sock.recv()
            network_inputs = Network_Inputs(game_data, rollout_results["actions"])
            print("Game data converted to:", network_inputs.get_flattened_game_data())

            if compute_action_asap_floats:
                compute_action_asap_floats = False
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
                    (
                        np.array(
                            network_inputs.get_input_data()
                        ),
                        np.array(
                            network_inputs.get_flattened_game_data()
                        )
                    ),
                    dtype=np.float32
                )
                print("Floats generated:", len(floats))

            if frames_processed > 0 and this_rollout_has_seen_t_negative:
                if frames_processed % 50 == 0:
                    instrumentation__between_run_steps += time.perf_counter_ns() - pc # time the run step took
            pc = time.perf_counter_ns()

            # ============================
            # BEGIN ON RUN STEP
            # ============================
            # print("game_manager rollout(): Shape of img:", rollout_results["frames"][-1].shape(), ": floats:", floats)
            (
                action_idx,
                action_was_greedy,
                q_value,
                q_values,
            ) = exploration_policy(rollout_results["frames"][-1], floats) # TODO: consider replacing list index with available variable resized_frame

            computed_action = config_copy.inputs[action_idx]  # determine next input

            # Oh, the joy of not knowing what this is for but putting it in anyway
            if n_th_action_we_compute == 0:
                end_race_stats["value_starting_frame"] = q_value
                for i, val in enumerate(np.nditer(q_values)):
                    end_race_stats[f"q_value_{i}_starting_frame"] = val

            rollout_results["race_completion"].append(game_data["race_data"]["race_completion_max"])
            rollout_results["input_w"].append(config_copy.inputs[action_idx][GCInputs["A"]])
            rollout_results["actions"].append(action_idx)
            rollout_results["action_was_greedy"].append(action_was_greedy)
            rollout_results["q_values"].append(q_values)
            rollout_results["state_float"].append(floats)

            n_th_action_we_compute += 1

            if frames_processed % (self.run_steps_per_action * config_copy.update_inference_network_every_n_actions) == 0:
                print("Updating network")
                update_network()

            if not self.timeout_has_been_set:
                # reset the ai for doing bad things for too long?
                self.timeout_has_been_set = True
            
            if frames_processed == 0 and (savestate_path != self.latest_map_path_requested):
                map_change_requested_time = frames_processed
                give_up_signal_has_been_sent = True

            if ((frames_processed > self.max_overall_duration_f or frames_processed > last_progress_improvement_f + self.max_minirace_duration_f) and not this_rollout_is_finished):
                print("This rollout has finished because you guys suck at your jobs")
                race_time = frames_processed
                face_finished = False
                end_race_stats["race_time_for_ratio"] = race_time
                end_race_stats["race_time"] = config_copy.cutoff_rollout_if_race_not_finished_within_duration_f
                rollout_results["race_time"] = race_time
                
                # Possibly rewind game state? Unnecessary until proven otherwise.
                this_rollout_is_finished = True
        return rollout_results, end_race_stats

