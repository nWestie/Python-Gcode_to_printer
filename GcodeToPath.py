import numpy as np
from dataclasses import dataclass
from tkinter.filedialog import askopenfilename
from matplotlib.widgets import Slider
from typing import Optional
from plotting import LivePlot3D
import time

######### <CONFIG> #########
GCode_filename = ""
# GCode_filename = "./gcode/1-Cube.gcode"
# GCode_filename = "./gcode/testing.gcode"
default_folder = "./gcode"
alloc_block_size = 5000  # size of block allocation
timestep = 50  # time between csv frames in ms
######### </CONFIG> #########

# time to beat: 70sec
# With 1000 row chunked allocations: 0.5sec
# With 5000 row chunked allocations: 0.45sec
# - Calling this good
# lineCoords: np.ndarray = np.zeros((0, 3))
path_steps: np.ndarray = np.empty((5000, 5))
act_size: int = 0  # current size of data in pathSteps


def main() -> int:
    global GCode_filename, path_steps, act_size

    if (not GCode_filename):
        GCode_filename = askopenfilename(initialdir=default_folder)
    printer: Printer = Printer()
    startTime: float = time.time()
    with open(GCode_filename, "r") as gcode:
        for line in (l.removesuffix('\n') for l in gcode):
            new_steps = printer.parse_line(line)
            if (new_steps is None or len(new_steps) == 0):
                continue
            # offset timestamp of new data
            new_steps[:, 0] += path_steps[act_size-1, 0]+timestep
            # allocate more space if needed
            while (act_size+len(new_steps) > len(path_steps)):
                path_steps = np.vstack([path_steps, np.empty((5000, 3))])
            # insert new steps into full list
            new_size = act_size+len(new_steps)
            path_steps[act_size:new_size, :] = new_steps
            act_size = new_size

    # Trim array to actual size
    path_steps = path_steps[:act_size]
    print("time:", time.time()-startTime)
    # print("Total lines:", i)
    print("Not implemented:")
    for k, v in printer.unimplemented_cmds.items():
        print(f"{k}: {v}")
    LivePlot3D((200, 200, 200), updater)
    return 0


def updater(frame: int, slider: Slider) -> np.ndarray:
    slider.valmax = len(path_steps)
    # show a range of
    return path_steps[slider.val:min(slider.val+100, len(path_steps)), 1:4]


def inch_to_mm(val: float) -> float:
    return val*25.4


class PrinterPos:
    # Represents moving to this position with the specified feedrate
    # All units are absolute mm
    def __init__(self, pos: np.ndarray = np.array([0., 0., 0.]), e: float = 0., feedrate: float = 0.):
        self.pos: np.ndarray = pos
        self.e: float = e  # extrusion
        self.feedrate: float = feedrate

    def copy(self) -> 'PrinterPos':
        return PrinterPos(self.pos.copy(), self.e, self.feedrate)


class Printer:
    def __init__(self) -> None:
        self.inch_units: bool = False  # true if in imperial system
        self.relative_move: bool = False  # if movements are relative
        self.relative_e: bool = False  # if Extrusion is relative
        self.state: PrinterPos = PrinterPos(np.array((0., 0, 0)), 0, 0)
        self.last_state: PrinterPos = PrinterPos(np.array((0., 0, 0)), 0, 0)
        # offsets used to ensure G92 zeroing can be handled.
        self.workspace_offsets: dict[str, float] = {
            'x': 0, 'y': 0, 'z': 0, 'e': 0}
        self.unimplemented_cmds: dict[str, int] = {}

    def parse_line(self, line: str) -> Optional[np.ndarray]:
        """Parses a single line of Gcode. Relevant state is stored by the Printer object. If the line is a move or delay, returns an array of position commands: [time, x, y, z, e]. Units are ms and mm respectively"""
        # Remove comments(everything after a semicolon)
        line = line.split(";")[0]
        if (not line):
            return None

        cmds = [x for x in line.split(' ') if len(x)]
        cmd = cmds[0].upper()
        if (cmd in ('G0', 'G1')):  # Basic movement
            self.last_state = self.state.copy()
            self.parse_movement(cmds)
            return self.generate_move_steps()
        elif (cmd in ('G4', 'M0', 'M1')):
            return self.generate_dwell_steps(cmds)
        elif (cmd == 'G90'):  # Absolute Movement
            self.relative_move = False
            self.relative_e = False
        elif (cmd == 'G91'):  # Relative Movement
            self.relative_move = True
            self.relative_e = True
        elif (cmd == 'M82'):  # Extruder Absolute
            self.relative_e = False
        elif (cmd == 'M83'):  # Extruder Relative
            self.relative_e = True
        elif (cmd == 'G20'):  # Imperial
            self.inch_units = True
        elif (cmd == 'G21'):  # Metric(mm)
            self.inch_units = False
        elif (cmd == 'G92'):
            self.updateOffsets(cmds)
        else:
            count: int = self.unimplemented_cmds.get(cmd, 0) + 1
            self.unimplemented_cmds[cmd] = count
        return None
# Temprature commands: 'M104', 'M140', 'M141', 'M190', 'M109', 'M191'
# Fan commands:        'M106', 'M107'
# Homing: G28
# Dwell:

    def generate_move_steps(self) -> np.ndarray:
        # feedrate is mm/min -> convert to time
        # dist/feedrate = time
        travel = self.state.pos - self.last_state.pos
        dist = np.linalg.norm(travel)
        # Feedrate in mm/min, so convert from min->millisec
        if (self.state.feedrate == 0):
            raise ValueError("Feedrate cannot be zero")
        travel_time = dist/self.state.feedrate*60*1000
        num_steps = int(np.ceil(travel_time/timestep))

        # build array
        steps = np.empty((num_steps, 5))
        # add range of timesteps
        steps[:, 0] = np.arange(0, timestep*num_steps, timestep)
        # interpolate between the two positions
        steps[:, 1:4] = np.linspace(
            self.last_state.pos, self.state.pos, num_steps, endpoint=False)
        steps[:, 4] = np.linspace(
            self.last_state.e, self.state.e, num_steps, endpoint=False)
        return steps

    def generate_dwell_steps(self, cmds: list[str]) -> np.ndarray:
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
        pos_arr = np.append(self.state.pos, self.state.e)
        pos_arr = pos_arr.reshape(1, 4).repeat(num_steps, axis=0)
        times = np.arange(0, timestep*num_steps,
                          timestep).reshape(num_steps, 1)
        return np.hstack([times, pos_arr])

    def parse_movement(self, cmds: list[str]) -> None:
        """Called for G0/1. Updates self.current_pos based on the movements specified in the Gcode line"""
        for cmd in cmds:
            # Split command to letter/number
            axis = cmd[0].lower()
            val = float(cmd[1:])
            # handle imperial units
            if (self.inch_units):
                val = inch_to_mm(val)

            if (axis in 'xyz'):
                # Offsets only are required in absolute mode, in relative mode,
                # all commands are offset from the last position,
                # so the workspace offset doesn't matter
                i = 'xyz'.index(axis)
                if (self.relative_move):
                    val += self.state.pos[i]
                else:
                    val += self.workspace_offsets[axis]
                self.state.pos[i] = val
            elif (axis == 'e'):
                if (self.relative_e):
                    val += self.state.e
                else:
                    val += self.workspace_offsets[axis]
                self.state.e = val
            elif (axis == 'f'):
                self.state.feedrate = val

    def updateOffsets(self, cmds: list[str]) -> None:
        """G92 Allows specifying the current position in relation to a newly defined coordinate system, offset from the machine coords. The offsets in XYZE for this coodinate space are stored."""
        for cmd in cmds:
            axis = cmd[0].lower()
            if (axis not in "xyze"):
                continue
            new_val = float(cmd[1:])
            if (self.inch_units):
                new_val = inch_to_mm(new_val)
            i = 'xyz'.index(axis)
            curr_pos = self.state.pos[i]
            # Setting new offset.
            # new_val is the position the Gcode specifies it should be currently, so the offset is calculated to do this. curr_pos is always in absolute machine coords, in mm.
            self.workspace_offsets[axis] = curr_pos - new_val


if __name__ == "__main__":
    exit(main())
