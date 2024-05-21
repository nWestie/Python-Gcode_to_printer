;TYPE:Custom
G90 ; use absolute coordinates
M83 ; extruder relative mode
G21 ; MM units

G1 X10 Y10 E10
G1 X20 E10
G1 X50 Y50
G1 X100
G1 Y100
G1 X50
G1 Y50
G92 X100 Y-20
G1 X50 Y0