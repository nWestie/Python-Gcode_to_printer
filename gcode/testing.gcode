;TYPE:Custom
G90 ; use absolute coordinates
M83 ; extruder relative mode
G21 ; MM units
G0 F5000
;line
G1 X10 Y10 E10
G1 X20 E10
G1 X50 Y50
;box
G92 X0 Y0

G1 X50
G1 Y20
G1 X0 F2000
G1 Y50
G1 X0 Y-20 Z50 F7000