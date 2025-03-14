from tkinter.filedialog import askopenfilename
from tkinter import Tk
import matplotlib.pyplot as plt
import math
import os
import sys
import numpy as np
from tkinter.filedialog import askopenfile
from matplotlib import pyplot as plt
import GcodeToPath
from accel_curves import acc_spline
from LivePlotting import LivePlot2D


def main():
    plotFromFile()
    # spline_gen()


def spline_gen():
    dt = GcodeToPath.timestep/1000
    x, vf = acc_spline(500, 100, 100)
    t = np.linspace(0,dt*len(x),len(x))
    
    x_dot = np.diff(x)/dt

    print(f"vf = {vf}")
    print(f"x_dot[-1] = {x_dot[-1]}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    ax1.plot(t, x, linestyle='-', marker='.', color='g')
    ax2.plot(t[:-1], x_dot, linestyle='-', marker='.', color='g')

    plt.grid(True)
    plt.show()

def plotFromFile():
    # Select and load the CSV file
    file_path = askopenfilename(filetypes=[("CSV files", "*.csv")],
                                initialdir="C:/Users/westn/OneDrive - Widener University/Research/Nagel Lab/Dual Stage 3D printer/pathCSVs")

    # Load the CSV file into a NumPy array
    data = np.genfromtxt(file_path, delimiter=',', skip_header=1)

    # Check the shape of the data to understand its structure
    print("Data shape:", data.shape)

    # Extract columns
    time = data[:, 0]/1000
    xREF = data[:, 1]
    xLRA = data[:, 5]
    xSRA = data[:, 7]
    yREF = data[:, 2]
    yLRA = data[:, 6]
    ySRA = data[:, 8]

    dt = time[1]-time[0]

    x_dot = np.diff(xREF)/dt
    y_dot = np.diff(yREF)/dt

    print(f"xSRA max: {np.max(np.abs(xSRA))}")
    print(f"ySRA max: {np.max(np.abs(ySRA))}")

    # Plotting columns
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    ax1.plot(time, xREF, linestyle='-', marker='', color='g')
    ax1.plot(time, yREF, linestyle='-', color='b')
    # ax1.plot(time, xSRA, linestyle='-', color='g')

    ax1.set_title('X vs time ')
    ax1.set_xlabel('time(s)')
    ax1.set_ylabel('x displacement(mm)')

    ax2.plot(time[:-1], x_dot, linestyle='-', color='g')
    ax2.plot(time[:-1], y_dot, linestyle='-', color='b')
    # ax2.plot(time, yLRA, linestyle='-', color='b')
    # ax2.plot(time, ySRA, linestyle='-', color='g')
    ax2.set_title('Velocity ')
    ax2.set_xlabel('time(s)')
    ax2.set_ylabel('velocity')

    plt.grid(True)
    plt.show()


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

if __name__ == "__main__":
    exit(main())
