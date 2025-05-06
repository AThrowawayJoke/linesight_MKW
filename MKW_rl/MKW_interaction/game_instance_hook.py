from dolphin import event, gui, controller, savestate # type: ignore
# Note that the program runs from the main linesight folder
from MKW_rl.MKW_interaction.MKW_interface import MKW_Interface
import time
import os
import sys
sys.path.append(os.path.expanduser("~") + "\\AppData\\Local\\programs\\python\\python312\\lib\\site-packages")

import psutil
from typing import List
import numpy
import cv2
from multiprocessing.connection import Listener
from config_files import config_copy

from MKW_rl.MKW_interaction.MKW_data_translate import *

HOST = "127.0.0.1"

class GameInstanceHook():
    def __init__(self, port=8478):
        self.desired_inputs = None
        self.last_desired_inputs = {}
        self.current_unprocessed_frame = None
        self.resized = None
        self.frame_counter = 0
        self.red = 0xffff0000
        self.listener = None
        self.conn = None
        self.game_data_initiated = False
        self.game_data_interface = MKW_Interface()
        self.port = port
        self.load_state_desired = False
        self.desired_savestate = None
        self.last_game_data = None

    def framedrawn_handler(self, width, height, data):
        # Wait for data necessary to determine what we want to do
        self.current_unprocessed_frame = (height, width, data)

        # print("Now waiting for new request")
        # https://stackoverflow.com/questions/38412887/how-to-send-a-list-through-tcp-sockets-python
        socket_data = self.conn.recv()
        # print("Received:", socket_data)

        frame_data_request = socket_data[0]
        game_data_request = socket_data[1]
        new_inputs = socket_data[2]
        load_state_request = socket_data[3]

        if new_inputs is not None:
            self.desired_inputs = new_inputs

        if load_state_request is not None:
            print("Got a request for savestate load:", socket_data[3])
            self.load_state_desired = True
            self.desired_savestate = socket_data[3]
            if frame_data_request:
                print("ERROR: Savestate file received but got unactionable frame data request")
            if game_data_request:
                print("ERROR: Savestate file received but got unactionable game data request")
            return

        if frame_data_request:
            self.conn.send_bytes(self.current_unprocessed_frame[2]) # unsure if i should pre-process frame or not...

            # width * height * 4, socket.MSG_WAITALL # server recv to receive frame data because it's big

            """# The following line brought to you by literal hours of trying to figure things out only to realize I just needed two functions that I could've just copied from the original code
            processed_frame = numpy.frombuffer(self.current_unprocessed_frame[2], dtype = numpy.uint8).reshape((self.current_unprocessed_frame[0], self.current_unprocessed_frame[1], 3))
            # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
            resized_frame = processed_frame[::6,::6]
            resized_frame = numpy.expand_dims(cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY), 0) # took me like 80 minutes to get to the solution that was already present in the original code
            # frame is a numpy array of shape (1, H, W) and dtype np.uint8
            print(processed_frame.shape, ":", resized_frame.shape)"""
        
        if game_data_request and self.desired_savestate is not None:
            if not self.game_data_initiated:
                self.game_data_interface.initialize_race_objects()
                self.game_data_initiated = True

            game_data = self.game_data_interface.get_game_data_object()
            for key in game_data["kart_data"].keys():
                value = game_data["kart_data"][key]
                if type(value) == vec3:
                    game_data["kart_data"][key] = [value.x, value.y, value.z]
            self.conn.send(game_data)
            self.last_game_data = game_data
        elif game_data_request:
            print("ERROR: game_data_request was sent before race state was loaded")
        # send the image data here, so we can set desired_inputs before we exit the function
            
    def frameadvance_handler(self):
        self.frame_counter += 1
        # draw on screen
        gui.draw_text((10, 10), self.red, f"Frame: {self.frame_counter}")

        if self.load_state_desired:
            self.load_state_desired = False
            savestate.load_from_file(self.desired_savestate)
            self.game_data_initiated = False
            # print("Loaded new savestate:", self.desired_savestate)

        if self.desired_inputs and self.desired_inputs != self.last_desired_inputs:
            # print("Applying inputs:", self.desired_inputs)
            controller.set_gc_buttons(0, self.desired_inputs)
            self.last_desired_inputs = self.desired_inputs

    def register(self):
        print("Initialize connection to Dolphin ")
        # self.iface = TMInterface(self.tmi_port) # reset the interface

        connection_attempts_start_time = time.perf_counter()
        last_connection_error_message_time = time.perf_counter()

        self.listener = Listener((HOST, self.port))
        print("Game hook socket listening on port", self.port)

        self.conn = self.listener.accept()
        print("Connected accepted from:", self.listener.last_accepted)

# Possibly send a packet through a known channel, which then establishes a separate connection?
# Or start at a known port and iterate until you find a clear one
def is_dolphin_process(process: psutil.Process) -> bool:
    try:
        return "Dolphin" in process.name()
    except psutil.NoSuchProcess:
        return False

def get_dolphin_pids() -> List[int]:
    return [process.pid for process in psutil.process_iter() if is_dolphin_process(process)]

# Use base tmi port, plus number of active dolphin instances (does not handle restarts correctly), minus 1 for this instance
mymanager = GameInstanceHook(config_copy.base_tmi_port + len(get_dolphin_pids()) - 1)
print("Working from port", mymanager.port)

"""
Register the socket, ensure it is connected
when framedrawn_handler is called, we read from the socket, waiting if necessary.
We process
    1. Whether a frame is requested, then sending data
    2. Whether any game data is requested, then sending data
    3. Whether to receive new inputs
Next, when frameadvance_handler is called
    1. Draw debug information to screen (inputs, framecount, fps?)
    2. Apply inputs to the game (if changed)
    3. Maybe write to a log file?

"""

mymanager.register()


event.on_framedrawn(mymanager.framedrawn_handler)
event.on_frameadvance(mymanager.frameadvance_handler)