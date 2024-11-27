from dolphin import event, gui, controller # type: ignore
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
        self.tm_process_id = None
        self.tm_window_id = None
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

    def launch_game(self):
        pass

    def is_MKW_process(self, process: psutil.Process) -> bool:
        try:
            return "Mario Kart Wii" in process.name()
        except psutil.NoSuchProcess:
            return False

    def get_MKW_pids(self) -> List[int]:
        return [process.pid for process in psutil.process_iter() if self.is_MKW_process(process)]

    def close_game(self):
        pass

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


