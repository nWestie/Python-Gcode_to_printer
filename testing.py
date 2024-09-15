import math
import os
import sys
import numpy as np
from tkinter.filedialog import askopenfile
from matplotlib import pyplot as plt

v = np.array([1, 2, 3, 4, 5, 6])
print(np.reshape(v, [v.size, 1]))


# Apply the convolution with 'full' mode (zero-padding at the edges)


# pos_arr = np.linspace((1, 2, 4), (1.2, 4.3, 1), 5)
# p = GCode_parser(2000)
# pos_arr = np.empty([0, 5])
# # pos_arr = p.parse_line("G1 X10 Y80.52 F5000")
# with open("gcode/testing.gcode", 'r') as f:
#     for line in f:
#         val = p._parse_line(line)
#         if (val is not None):
#             pos_arr = np.vstack((pos_arr, val))


# def updater(frame: int, s: Slider) -> np.ndarray:
#     return pos_arr[:, 1:4] if (pos_arr is not None) else np.zeros((1, 3))


# LivePlot3D((200, 200, 200), updater)
# print(pos_arr)
# print(len(pos_arr))
# pos_arr = p.parse_line("G4 P550")
# print(pos_arr)
