from dolphin import event, gui, controller, savestate, memory # type: ignore
from config_files import config_copy, user_config

red = 0xffff0000
frame_counter = 0

async def my_callback():
    global frame_counter
    frame_counter += 1
    # draw on screen
    gui.draw_text((10, 10), red, f"Frame: {frame_counter}")
    # print to console
    # print("we are working!" + frame_counter)
    if frame_counter % 60 == 0:
        print(f"The frame count has reached {frame_counter}")
        gc_controller = controller.get_gc_buttons(0)
        gc_controller["A"] = True
        controller.set_gc_buttons(0, gc_controller)
        await event.frameadvance()
        frame_counter += 1
        gc_controller["A"] = False
        controller.set_gc_buttons(0, gc_controller)

event.on_frameadvance(my_callback)

import math
import os
import socket
import subprocess
import time
from typing import Callable, Dict, List

import cv2
import numba
import numpy as np
import numpy.typing as npt
import psutil
import dxcam

import win32.lib.win32con as win32con
import win32com.client
import win32gui
import win32process

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
        self.latest_tm_engine_speed_requested = 1
        self.running_speed = running_speed
        self.run_steps_per_action = run_steps_per_action
        self.max_overall_duration_ms = max_overall_duration_ms
        self.max_minirace_duration_ms = max_minirace_duration_ms
        self.timeout_has_been_set = False
        self.msgtype_response_to_wakeup_TMI = None
        self.latest_map_path_requested = -2
        self.last_rollout_crashed = False
        self.last_game_reboot = time.perf_counter()
        self.UI_disabled = False
        self.tmi_port = tmi_port
        self.dolphin_process_id = None
        self.dolphin_window_id = None
        self.start_states = {}
        self.game_spawning_lock = game_spawning_lock
        self.game_activated = False
        self.camera = dxcam.create(output_idx=0, output_color="GRAY")
    
    def get_window_id(self):
        assert self.tm_process_id is not None

        if config_copy.is_linux:
            """self.tm_window_id = None
            while self.tm_window_id is None:  # This outer while is for the edge case where the window may not have had time to be launched
                window_search_depth = 1
                while True:  # This inner while is to try and find the right depth of the window in Xdo().search_windows()
                    c1 = set(Xdo().search_windows(winname=b"TrackMania Modded", max_depth=window_search_depth + 1))
                    c2 = set(Xdo().search_windows(winname=b"TrackMania Modded", max_depth=window_search_depth))
                    c1 = {w_id for w_id in c1 if Xdo().get_pid_window(w_id) == self.tm_process_id}
                    c2 = {w_id for w_id in c2 if Xdo().get_pid_window(w_id) == self.tm_process_id}
                    c1_diff_c2 = c1.difference(c2)
                    if len(c1_diff_c2) == 1:
                        self.tm_window_id = c1_diff_c2.pop()
                        break
                    elif (
                        len(c1_diff_c2) == 0 and len(c1) > 0
                    ) or window_search_depth >= 10:  # 10 is an arbitrary cutoff in this search we do not fully understand
                        print(
                            "Warning: Worker could not find the window of the game it just launched, stopped at window_search_depth",
                            window_search_depth,
                        )
                        break
                    window_search_depth += 1"""
            pass
        else:

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
                for hwnd in get_hwnds_for_pid(self.tm_process_id):
                    if "Mario Kart Wii" in win32gui.GetWindowText(hwnd):
                        self.tm_window_id = hwnd
                        return
                # else:
                #     raise Exception("Could not find TmForever window id.")

    # Launch program and return pids
    def launch_game(self):
        self.tm_process_id = None

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
                f'\'--video_backend="{user_config.video_backend}" --exec="{user_config.game_path}"\';'
                ' echo exit $process.id}"' # push process_id to stdout to read later
            )

            
            dolphin_process_id = int(subprocess.check_output(launch_string).decode().split("\r\n")[1]) # locate the pid from the program
            while self.tm_process_id is None:
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
                        self.tm_process_id = process_id
                        break

        print(f"Found Trackmania process id: {self.tm_process_id=}")
        self.last_game_reboot = time.perf_counter() # set counter to know how old the process is
        self.latest_map_path_requested = -1
        self.msgtype_response_to_wakeup_TMI = None
        while not self.is_game_running(): # wait for the program to launch fully
            time.sleep(0)

        self.get_MKW_window_id() # locate window ID for the process

    def is_MKW_process(self, process: psutil.Process) -> bool:
        try:
            return "Mario Kart Wii" in process.name() # TODO: Adjust for game variability
        except psutil.NoSuchProcess:
            return False

    def get_MKW_pids(self) -> List[int]:
        return [process.pid for process in psutil.process_iter() if self.is_MKW_process(process)]

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

    # Using Felk fork. Outdated
    def grab_screen(self): # add pid parameter
        left, top = (2560 - 640) // 2, (1440 - 640) // 2 # pull dimensions from pid
        right, bottom = left + 640, top + 640
        region = (left, top, right, bottom)
        large_image = self.camera.grab(region=region) # dxcam
        input_size = 640
        output_size = 128
        bin_size = input_size # output_size
        small_image = large_image.reshape((1, output_size, bin_size,
                                      output_size, bin_size)).max(4).max(2)
        return small_image

    async def grab_felk_screen(self):
        pass
        large_image = event.frameadvance()

