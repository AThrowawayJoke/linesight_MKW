from dolphin import event, gui, controller, savestate # type: ignore
# Note that the program runs from the main linesight folder
from MKW_rl.MKW_interaction.game_data_interface import Game_Data_Interface
import time
import os
import sys
sys.path.append(os.path.expanduser("~") + "\\AppData\\Local\\programs\\python\\python312\\lib\\site-packages")

import numpy
import cv2
import socket
import pickle

HOST = "127.0.0.1"

class GameInstanceHook():
    def __init__(self, port=65432):
        self.desired_inputs = None
        self.last_desired_inputs = {}
        self.current_unprocessed_frame = None
        self.resized = None
        self.frame_counter = 0
        self.red = 0xffff0000
        self.listener = None
        self.conn = None
        self.game_data_interface = Game_Data_Interface()
        self.port = port

    def framedrawn_handler(self, width, height, data):
        # Wait for data necessary to determine what we want to do
        self.current_unprocessed_frame = (height, width, data)

        # https://stackoverflow.com/questions/38412887/how-to-send-a-list-through-tcp-sockets-python
        socket_data = pickle.loads(self.conn.recv(4096))
        print("Received:", socket_data)

        frame_data_request = socket_data[0]
        game_data_request = socket_data[1]
        new_inputs = socket_data[2]
        load_state_request = socket_data[3]

        if new_inputs is not None:
            self.desired_inputs = new_inputs

        if load_state_request is not None:
            print("Attempting to load new savestate with file location:", socket_data[3])
            savestate.load_from_file(socket_data[3])
            if frame_data_request:
                print("ERROR: Savestate file received but got unactionable frame data request")
            if game_data_request:
                print("ERROR: Savestate file received but got unactionable game data request")
            return

        if frame_data_request:
            self.conn.sendall(self.current_unprocessed_frame) # unsure if i should pre-process frame or not...

            # width * height * 4, socket.MSG_WAITALL # server recv to receive frame data because it's big

            """# The following line brought to you by literal hours of trying to figure things out only to realize I just needed two functions that I could've just copied from the original code
            processed_frame = numpy.frombuffer(self.current_unprocessed_frame[2], dtype = numpy.uint8).reshape((self.current_unprocessed_frame[0], self.current_unprocessed_frame[1], 3))
            # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
            resized_frame = processed_frame[::6,::6]
            resized_frame = numpy.expand_dims(cv2.cvtColor(resized_frame, cv2.COLOR_BGRA2GRAY), 0) # took me like 80 minutes to get to the solution that was already present in the original code
            # frame is a numpy array of shape (1, H, W) and dtype np.uint8
            print(processed_frame.shape, ":", resized_frame.shape)"""
        
        if game_data_request:
            kart_pos_rot = self.game_data_interface.get_kart_position_and_rotation()
            kart_velocity = self.game_data_interface.get_kart_velocities() # Returns dicti of 4 vectors, "external_velocity", "internal_velocity", "moving_road_velocity", and "moving_water_velocity"
            checkpoint_data = self.game_data_interface.get_checkpoint_data()
            driving_direction = self.game_data_interface.get_driving_direction() # likely not useful
            item_count = self.game_data_interface.get_item_count()
            self.conn.sendall(pickle.dumps([kart_pos_rot, kart_velocity, checkpoint_data, driving_direction, item_count]))
        # send the image data here, so we can set desired_inputs before we exit the function
            
    def frameadvance_handler(self):
        self.frame_counter += 1
        # draw on screen
        gui.draw_text((10, 10), self.red, f"Frame: {self.frame_counter}")

        if self.desired_inputs and self.desired_inputs != self.last_desired_inputs:
            controller.set_gc_buttons(0, self.desired_inputs)
            self.last_desired_inputs = self.desired_inputs

    def register(self, port):
        print("Initialize connection to Dolphin ")
        # self.iface = TMInterface(self.tmi_port) # reset the interface

        connection_attempts_start_time = time.perf_counter()
        last_connection_error_message_time = time.perf_counter()

        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.listener.bind(HOST, self.port)
        print("Game hook socket binded on port", self.port)

        self.listener.listen(1)
        self.conn, addr = self.listener.accept()
        print("Connected. Address:", addr)


mymanager = GameInstanceHook()

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