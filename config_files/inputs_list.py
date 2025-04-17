from dolphin import controller # type: ignore

from mkw_scripts.Modules.mkw_classes import player_stats

"""
When creating a list of inputs, several considerations must be made to help reduce the amount of options available to the ai.
IQN uses discrete inputs. It only chooses one option out of the following list to perform for any given frame.
Thus, too many inputs will complicate the network and at some point slow down training significantly. More testing need to be done to find the limit of this.
For now (e.g. until someone gets around to testing it), it is recommended to keep the number of input combinations to below 20.

Therefore, when selecting inputs, consider the following:
    1. Soft-drifting charges a mini-turbo at the fastest rate while turning the least amount. This value is -3 and 3 and should be present as an option in the inputs for optimized times.
    2. Using an item rarely needs to use more than one input for Time Trials, as you can simply match what should be pressed when a given track's shroom strat happens.
    3. only inputs deviating from the default state need to be present. It is possible that my implementation is getting optimized when compiling.
    4. Start alignments are useful, though they only have an impact in the first ~1.5 seconds of a run so long as it's not playing DK Summit.
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

defaultInputState = {
    controller.GCInputs.A: False,
    controller.GCInputs.B: False,
    controller.GCInputs.X: False,
    controller.GCInputs.Y: False,
    controller.GCInputs.Z: False,
    controller.GCInputs.Start: False,
    controller.GCInputs.Up: False,
    controller.GCInputs.Down: False,
    controller.GCInputs.Left: False,
    controller.GCInputs.Right: False,
    controller.GCInputs.L: False,
    controller.GCInputs.R: False,
    controller.GCInputs.StickX: 113,
    controller.GCInputs.StickY: 113,
    controller.GCInputs.CStickX: 0,
    controller.GCInputs.CStickY: 0,
    controller.GCInputs.TriggerLeft: 0,
    controller.GCInputs.TriggerRight: 0
}

# Adjust for individual tracks for item usage or other things
inputs = [
    {  # 0 Forward
        controller.GCInputs.A: True
    },
    {  # 1 Drift full left
        controller.GCInputs.A: True,
        controller.GCInputs.StickX: 0,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 2 Drift full right
        controller.GCInputs.StickX: 255,
        controller.GCInputs.A: True,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 3 Drift slight left
        controller.GCInputs.A: True,
        controller.GCInputs.StickX: 90,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 4 Drift slight right
        controller.GCInputs.A: True,
        controller.GCInputs.StickX: 170,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 5 Drift straight
        controller.GCInputs.A: True,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 6 Drift full right item # TODO: Adjust for individual tracks based on item usage
        controller.GCInputs.StickX: 255,
        controller.GCInputs.A: True,
        controller.GCInputs.TriggerRight: 1,
        controller.GCInputs.TriggerLeft: 1,
    },
    {  # 7 Full left # Note that #7 and #8 may not be necessary for all tracks, but are useful for alignment in wheelies.
        controller.GCInputs.StickX: 0,
        controller.GCInputs.A: True,
    },
    {  # 8 Full right
        controller.GCInputs.StickX: 255,
        controller.GCInputs.A: True,
    },
    {  # 9 Trick straight
        controller.GCInputs.Up: True,
        controller.GCInputs.A: True,
    },
    {  # 10 Trick full right
        controller.GCInputs.Up: True,
        controller.GCInputs.A: True,
        controller.GCInputs.StickX: 255,
    },
    {  # 11 Trick full left
        controller.GCInputs.StickX: 0,
        controller.GCInputs.Up: True,
        controller.GCInputs.A: True,
    },
    {  # 12 No Accel (Start boost) # Note that stick is in default position
        controller.GCInputs.A: False,
    },
    {  # 13 No Accel right (Start maneuvering)
        controller.GCInputs.StickX: 255,
        controller.GCInputs.A: False,
        controller.GCInputs.TriggerRight: 1,
    },
    {  # 14 No Accel left (Start maneuvering)
        controller.GCInputs.StickX: 0,
        controller.GCInputs.A: False,
        controller.GCInputs.TriggerRight: 1,
    },
]

action_forward_idx = 0  # Accelerate forward, don't turn
action_backward_idx = 12  # Don't move, don't turn
