"""
This file defines the game ID to use for all scripts in mkw-scripts
The game ID is dependent on the region of your game file.

If unsure, check the flag Dolphin displays in the menu and match it with the value in quotations below.
USA: NTSC-U -- "RMCE01"
Europe: PAL -- "RMCP01"
Japan: NTSC-J -- "RMCJ01"
Republic of Korea: NTSC-K -- "RMCK01"
"""

game_id_string = "RMCE01"

# Private variable to avoid confusion in usage
__address = {"RMCE01": 0x809BF0B8, "RMCP01": 0x809C38C0,
    "RMCJ01": 0x809C2920, "RMCK01": 0x809B1F00}

address_id = __address[game_id_string]

