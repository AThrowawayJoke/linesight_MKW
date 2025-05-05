from typing import TypedDict

class GCInputs(TypedDict, total=False):
    """
    Dictionary describing the state of a GameCube 
    Boolean keys (buttons): True means pressed, False means released.
    Float keys for triggers: 0 means fully released, 1 means fully pressed.
    Float keys for sticks: 0 means neutral, ranges from -1 to 1.
    """
    A: bool
    B: bool
    X: bool
    Y: bool
    Z: bool
    Start: bool
    Up: bool
    Down: bool
    Left: bool
    Right: bool
    L: bool
    R: bool
    StickX: float
    StickY: float
    CStickX: float
    CStickY: float
    TriggerLeft: float
    TriggerRight: float

"""
When creating a list of inputs, several considerations must be made to help reduce the amount of options available to the ai.
IQN uses discrete inputs. It only chooses one option out of the following list to perform for any given frame.
Thus, too many inputs will complicate the network and at some point slow down training in theory. Testing needs to be done to find the amount of slowdown, if any.
For now (e.g. until I get around to testing it), it is recommended to keep the number of input combinations to below 20.

Therefore, when selecting inputs, consider the following:
    1. Soft-drifting charges a mini-turbo at the fastest rate while turning the least amount. This value is -3 and 3 and should be present as an option in the inputs for optimized times.
    2. Using an item rarely needs to use more than one input for Time Trials, as you can simply match what should be pressed when a given track's shroom strat happens.
    3. only the inputs deviating from the default state need to be present (i.e the 'X' and 'Y' buttons are never used, so they are omitted), however all used buttons should be present in all states.
    4. Non-accelerating inputs (used for start alignments) are useful, even if only for the first ~1.5 seconds of a run so long as it's not playing DK Summit (Slowdown for double cut strat).
    5. More stick options will likely give small improvements to times, although human WRs rarely use them, if at all. Remains to be tested.
        (Note that the base game simplifies down to 15 unique values for steering, ranging from -7 to 7)
    6. It is useful on certain tracks to cancel wheelies with D-pad down, on tracks such as rPB, rSL, and rBC.
"""

""" 
GCInputs type list
    A: bool
    B: bool
    X: bool
    Y: bool
    Z: bool
    Start: bool
    Up: bool
    Down: bool
    Left: bool
    Right: bool
    L: bool
    R: bool
    StickX: float
    StickY: float
    CStickX: float
    CStickY: float
    TriggerLeft: float
    TriggerRight: float
    
Stick value conversion for GCInputs:
    (14) 205-255 (+7) Full Right
    (13) 197-204 (+6)
    (12) 188-196 (+5)
    (11) 179-187 (+4)
    (10) 170-178 (+3) Soft Right
    (9) 161-169 (+2)
    (8) 152-160 (+1)
    (7) 113-151 (+0) Neutral
    (6) 105-112 (-1)
    (5) 96-104 (-2)
    (4) 87-95 (-3) Soft Left
    (3) 78-86 (-4)
    (2) 69-77 (-5)
    (1) 60-68(-6)
    (0) 0-59 (-7) Full Left
"""

defaultInputState: GCInputs = {
    "A": False,
    "B": False,
    "Up": False,
    "StickX": 113,
    "StickY": 113,
    "TriggerLeft": 0,
    "TriggerRight": 0
}

# Adjust for individual tracks for item usage or other things
inputs = [
    {  # 0 Forward
        "A": True,
        "B": False,
        "Up": False,
        "StickX": 113,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 1 Drift full left
        "A": True,
        "StickX": 0,
        "TriggerRight": 1,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 2 Drift full right
        "StickX": 255,
        "A": True,
        "TriggerRight": 1,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 3 Drift slight left
        "A": True,
        "StickX": 90,
        "TriggerRight": 1,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 4 Drift slight right
        "A": True,
        "StickX": 170,
        "TriggerRight": 1,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 5 Drift straight
        "A": True,
        "TriggerRight": 1,
        "B": False,
        "Up": False,
        "StickX": 113,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 6 Drift full right item # TODO: Adjust for individual tracks based on item usage
        "StickX": 255,
        "A": True,
        "TriggerRight": 1,
        "TriggerLeft": 1,
        "B": False,
        "Up": False,
        "StickY": 113,
    },
    {  # 7 Full left # Note that inputs #7 and #8 may not be necessary for all tracks, but are useful for alignment after wheelies.
        "StickX": 0,
        "A": True,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 8 Full right
        "StickX": 255,
        "A": True,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 9 Trick straight
        "Up": True,
        "A": True,
        "B": False,
        "StickX": 113,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 10 Trick full right
        "Up": True,
        "A": True,
        "StickX": 255,
        "B": False,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 11 Trick full left
        "StickX": 0,
        "Up": True,
        "A": True,
        "B": False,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 12 No Accel (Start boost) # Note that stick is in default position
        "A": False,
        "B": False,
        "Up": False,
        "StickX": 113,
        "StickY": 113,
        "TriggerLeft": 0,
        "TriggerRight": 0
    },
    {  # 13 No Accel right (Start maneuvering)
        "StickX": 255,
        "TriggerRight": 1,
        "A": False,
        "B": False,
        "Up": False,
        "StickY": 113,
        "TriggerLeft": 0,
    },
    {  # 14 No Accel left (Start maneuvering)
        "StickX": 0,
        "StickY": 113,
        "TriggerRight": 1,
        "A": False,
        "B": False,
        "Up": False,
        "TriggerLeft": 0,
    },
]

action_forward_idx = 0  # Accelerate forward, don't turn
action_backward_idx = 12  # Don't move, don't turn
