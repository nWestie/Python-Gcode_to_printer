from datetime import datetime
import math
import sys
import numpy as np
from dataclasses import dataclass
from tkinter.filedialog import askopenfilenames
from matplotlib.widgets import Slider
from functools import partial
from typing import Optional
from LivePlotting import LivePlot3D
import time
import os


######### <CONFIG> #########
# GCode_filenames = "../gcode/x-triwave-150mm.gcode",
output_folder = "../pathCSVs/"
feedrate_override = 1000  # in mm/s
cutoff_freq = 20  # In Hz, for second order filter
default_folder = "../gcode"
show_plot = False
alloc_block_size = 5000  # size of block allocation
timestep: float = 1.0  # time between csv frames in ms

acceleration = 40000  # in mm/s^2
max_velocity = 2000  # in mm/s
corner_velocity = 300  # in mm/s

######### </CONFIG> #########

import accel_curves # This must be down here to allow accel_curves to be run independantly (since it uses some config vars)

class PathArray:
    """An array of points, at a constant timestep for X,Y,Z, and E axes"""

    def __init__(self):
        self._steps: np.ndarray = np.zeros((1, 5))
        self._act_size = 0
        self._add_space()

    def append(self, new_steps: np.ndarray):
        """Add rows to the PathArray: new_steps is a [N,4] array of the X, Y, Z and E positions"""
        # Check that there is enough space to add new_steps
        if (self._act_size+len(new_steps) > len(self._steps)):
            self._add_space()
        # Update length and append the steps
        new_size = self._act_size+len(new_steps)
        self._steps[self._act_size:new_size, 1:] = new_steps
        self._act_size = new_size

    def size(self):
        return self._act_size

    def get(self):
        return self._steps[:self._act_size]

    def _add_space(self):
        """Add additional rows to the PathArray. The time column is filled at this point as well."""
        next_time = self._steps[-1, 0] + timestep
        self._steps = np.vstack([self._steps, np.empty((alloc_block_size, 5))])
        self._steps[-alloc_block_size:,
                    0] = np.arange(next_time, next_time+timestep*alloc_block_size, timestep)

    def trim(self):
        """Remove the blank, unfilled steps at the end of the list"""
        self._steps = self._steps[:self._act_size]


def updater(frame: int, slider: Slider, pathArr: PathArray) -> np.ndarray:
    slider.valmax = pathArr.size()
    # show a range of values
    return pathArr.get()[slider.val:min(slider.val+500, pathArr.size()), 1:4]


def main() -> int:
    global plottedPath, feedrate_override, GCode_filenames

    # make sure the script folder is the working dir
    os.chdir(os.path.dirname(__file__))
    # check if filename provided as arg
    Prusa_output_name_override = None
    if (len(sys.argv) > 1):
        GCode_filenames = sys.argv[1],
        # overwrite feedrate from PrusaSlicer if it exists
        feedrate_override = int(os.environ.get(
            "SLIC3R_PERIMETER_SPEED") or feedrate_override)
        Prusa_output_name_override = os.environ.get("SLIC3R_PP_OUTPUT_NAME")

    elif ('GCode_filenames' not in globals() or len(GCode_filenames) == 0):
        GCode_filenames = askopenfilenames(initialdir=default_folder)

    for file_name in GCode_filenames:
        # Generate paths

        # Default feedrate set to 2000 mm/min for now
        print()
        print(file_name)
        printer: GCode_parser = GCode_parser(2000)
        startTime: float = time.time()
        path = printer.parse_file(file_name)

        pathArray = path.get()
        # applying second order non-causal filter
        x_lra = np.reshape(second_order_smooth(
            pathArray[:, 1], cutoff_freq).T, [path.size(), 1])
        y_lra = np.reshape(second_order_smooth(
            pathArray[:, 2], cutoff_freq), [path.size(), 1])
        pathArray = np.hstack([pathArray, x_lra, y_lra])
        x_sra = (pathArray[:, 1] - pathArray[:, 5])
        x_sra = x_sra[:, np.newaxis]
        y_sra = (pathArray[:, 2] - pathArray[:, 6])
        y_sra = y_sra[:, np.newaxis]
        pathArray = np.hstack([pathArray, x_sra, y_sra])

        print("Parse time:", time.time()-startTime)
        print("Total lines:", np.size(path.size()))

        # print("Not implemented:")
        # for k, v in printer.unimplemented_cmds.items():
        #     print(f"- {k}: {v}")

    # Visualizing
        if (show_plot):
            LivePlot3D((200, 200, 200), partial(updater, pathArr=path))

    # Write file:
        startTime = time.time()
        timestamp = datetime.now().strftime('Date %y-%m-%d Time %H:%M:%S')

        # If triggered from PrusaSlicer, override temp filename with the destination filename
        if (Prusa_output_name_override):
            file_name = Prusa_output_name_override
            print(Prusa_output_name_override)
        out_filename = os.path.basename(file_name)
        out_filename = output_folder + \
            os.path.splitext(out_filename)[
                0] + f"-{corner_velocity}mms_min-{max_velocity}mms_max"
        np.savetxt(out_filename+".csv", pathArray,
                   delimiter=",", fmt='%.3f', header="t(ms), xRef, yRef, z, e, xLRA, yLRA, xSRA, ySRA")

        size_str = size_as_str(os.path.getsize(out_filename+".csv"))
        print(f"saved to {out_filename}.csv")

    # Create sidecar file with additional data
        with open(out_filename+".txt", 'w') as sidecar:
            sidecar.write(f"Main File: {out_filename}.csv\n")
            sidecar.write(f"Main File Size: {size_str}\n")
            sidecar.write(f"Created: {timestamp}\n")
            sidecar.write(f"2nd Order Cutoff Freq: {cutoff_freq}Hz\n")
            sidecar.write(f"Corner Velocity: {corner_velocity} mm/s\n")
            sidecar.write(f"Max Velocity: {max_velocity} mm/s\n")
            sidecar.write(f"Acceleration: {acceleration} mm/s\n")
            sidecar.write(f"Total path points: {path.size()}\n")
            sidecar.write(f"Timestep: {timestep}ms\n")
            sidecar.write(f"Total Time: {timestep*path.size()/1000}s")
        print(f"saved to {os.path.abspath(out_filename)}.txt")
        print(f"Size:{size_str}")

        print("save time:", time.time()-startTime)

    return 0


def second_order_smooth(sequence, cutoff_freq):
    """Cutoff Freq. in Hz"""
    alpha = calc_smoothing(cutoff_freq, timestep*1000)  # Timestep is in ms
    smoothed = exp_smooth(sequence, alpha)
    # return smoothed
    return np.flip(exp_smooth(np.flip(smoothed), alpha))


def calc_smoothing(f_cutoff, f_sample) -> float:
    """Calculate alpha, the exp. smoothing value for a rolling IIR filter.\n
    Frequencies are in Hz"""
    # Sources: https://www.dsprelated.com/showarticle/182.php, https://dsp.stackexchange.com/a/40465
    x = 2*math.pi*f_cutoff/f_sample
    return math.cos(x) - 1 + math.sqrt(math.pow(math.cos(x), 2) - 4*math.cos(x) + 3)


def exp_smooth(sequence, alpha):
    out = np.zeros(np.size(sequence))
    # for i=0 case, will be overwritten
    out[-1] = sequence[0]
    for i, val in enumerate(sequence):
        out[i] = (1-alpha)*out[i-1]+alpha*val
    return out


def inch_to_mm(val: float) -> float:
    return val*25.4


class GCode_parser:
    def __init__(self, default_feedrate: float) -> None:
        """Init a gcode parser with the specified default feedrate"""

        # Public path
        self.path: PathArray = PathArray()

        self._inch_units: bool = False  # true if in imperial system
        self._relative_move: bool = False  # if movements are relative
        self._relative_e: bool = False  # if Extrusion is relative
        self._feedrate: float = default_feedrate
        self._state: np.ndarray = np.zeros(4)  # X, Y, Z, and E positions
        self._last_state: np.ndarray = np.zeros(4)  # Prev state
        # offsets used to ensure G92 zeroing can be handled.
        self.workspace_offsets: np.ndarray = np.zeros(4)
        self.unimplemented_cmds: dict[str, int] = {}

    def get_axis_index(self, axis: str) -> int:
        """Converts the axis letter to the index needed for state and offsets"""
        return 'xyze'.index(axis)

    def parse_file(self, filename: str) -> PathArray:
        with open(filename, "r") as gcode:
            for line in (l.removesuffix('\n') for l in gcode):
                self._parse_line(line)
        # Trim array to actual size
        self.path.trim()
        return self.path

    def _parse_line(self, line: str):
        """Parses a single line of Gcode. Relevant state is stored by the Printer object. If the line is a move or delay, returns an array of position commands: [time, x, y, z, e]. Units are ms and mm respectively"""
        # Remove comments(everything after a semicolon)
        line = line.split(";")[0]
        if (not line):
            return None

        cmds = [x for x in line.split(' ') if len(x)]
        cmd = cmds[0].upper()

        if (cmd in ('G0', 'G1')):  # Basic movement
            self._last_state = self._state.copy()
            self._parse_movement(cmds)
            self._generate_move_steps()
            return
        elif (cmd in ('G4', 'M0', 'M1')):
            return self._generate_dwell_steps(cmds)

        elif (cmd == 'G90'):  # Absolute Movement
            self._relative_move = False
            self._relative_e = False
        elif (cmd == 'G91'):  # Relative Movement
            self._relative_move = True
            self._relative_e = True
        elif (cmd == 'M82'):  # Extruder Absolute
            self._relative_e = False
        elif (cmd == 'M83'):  # Extruder Relative
            self._relative_e = True
        elif (cmd == 'G20'):  # Imperial
            self._inch_units = True
        elif (cmd == 'G21'):  # Metric(mm)
            self._inch_units = False
        elif (cmd == 'G92'):
            self.updateOffsets(cmds)
        else:
            count: int = self.unimplemented_cmds.get(cmd, 0) + 1
            self.unimplemented_cmds[cmd] = count
        return None
# Temprature commands: 'M104', 'M140', 'M141', 'M190', 'M109', 'M191'
# Fan commands:        'M106', 'M107'
# Homing: G28

    def _generate_move_steps(self) -> None:
        # dist/feedrate = time
        travel = self._state - self._last_state
        # Euclydian distance of X and Y
        dist = float(np.linalg.norm(travel[:2]))
        angle = np.arctan2(travel[1], travel[0]) # get angle of path segment
        z_dist = float(travel[2])
        e_dist = float(travel[3])
        # interpolate between the two positions,
        # using acceleration and deceleration in X and Y
        # TODO: End vel is not handled properly, should probably be stored and used to adjust next move
        easing, end_vel = accel_curves.acc_spline(
            dist, corner_velocity, corner_velocity)
        norm_ease = easing/dist
        # Note - lists are stacked then transposed to match the rest of the data
        points = np.vstack((np.cos(angle)*easing, np.sin(angle)*easing,
                           z_dist*norm_ease, e_dist*norm_ease)).T
        
        points = points + self._last_state
        self.path.append(points)
        return
        # OLD - linear interpolation version
        # Feedrate in mm/s, so convert from sec->millisec
        feed = feedrate_override
        travel_time = dist/feed*1000
        num_steps = int(np.ceil(travel_time/timestep))
        self.path.append(np.linspace(
            self._last_state, self._state, num_steps, endpoint=False))

    def _generate_dwell_steps(self, cmds: list[str]):
        delay: float = 0.0  # in milliseconds
        for cmd in cmds:
            # S command takes precedence, if both are specified
            if (cmd[0].lower() == 's'):
                delay = float(cmd[1:]) * 1000
                break
            if (cmd[0].lower() == 'p' and delay == 0.0):
                delay = float(cmd[1:])

        # Build array
        num_steps = int(np.ceil(delay/timestep))
        self.path.append(self._state.reshape(1, 4).repeat(num_steps, axis=0))

    def _parse_movement(self, cmds: list[str]) -> None:
        """Called for G0/1. Updates self.current_pos based on the movements specified in the Gcode line"""
        for cmd in cmds:
            # Split command to letter/number
            axis = cmd[0].lower()
            val = float(cmd[1:])
            # handle imperial units
            if (self._inch_units):
                val = inch_to_mm(val)

            if (axis in 'xyz'):
                # Offsets only are required in absolute mode, in relative mode,
                # all commands are offset from the last position,
                # so the workspace offset doesn't matter
                i = self.get_axis_index(axis)
                if (self._relative_move):
                    val += self._state[i]
                else:
                    val += self.workspace_offsets[i]
                self._state[i] = val
            elif (axis == 'e'):
                if (self._relative_e):
                    val += self._state[3]
                else:
                    val += self.workspace_offsets[3]
                self._state[3] = val
            elif (axis == 'f'):
                self._feedrate = val

    def updateOffsets(self, cmds: list[str]) -> None:
        """G92 Allows specifying the current position in relation to a newly defined coordinate system, offset from the machine coords. The offsets in XYZE for this coodinate space are stored."""
        for cmd in cmds:
            axis = cmd[0].lower()
            if (axis not in "xyze"):
                continue
            new_val = float(cmd[1:])
            if (self._inch_units):
                new_val = inch_to_mm(new_val)
            i = self.get_axis_index(axis)
            curr_pos = self._state[i]
            # Setting new offset.
            # new_val is the position the Gcode specifies it should be currently, so the offset is calculated to do this. curr_pos is always in absolute machine coords, in mm.
            self.workspace_offsets[i] = curr_pos - new_val


def size_as_str(size_bytes: int) -> str:
    """
    Convert the file size from bytes to a human-readable format.

    Parameters:
    size_bytes (int): Size of the file in bytes.

    Returns:
    str: Human-readable file size.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


if __name__ == "__main__":
    # feedrates = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400]
    # feedrates = [405, 1300, 1400]

    # for feed in feedrates:
    #     feedrate_override = feed
    #     main()
    exit(main())
