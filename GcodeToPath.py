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
timestep = 100  # time between csv frames in ms
######### </CONFIG> #########


# path_steps: np.ndarray = np.empty((5000, 5))
# act_size: int = 0  # current size of data in pathSteps


class PathArray:
    def __init__(self):
        self._steps: np.ndarray = np.zeros((1, 5))
        self._act_size = 0
        self._add_space()

    def append(self, new_steps: np.ndarray):
        if (self._act_size+len(new_steps) > len(self._steps)):
            self._add_space()
        new_size = self._act_size+len(new_steps)
        path._steps[self._act_size:new_size, 1:] = new_steps
        self._act_size = new_size

    def get(self):
        return self._steps[:self._act_size]

    def _add_space(self):
        next_time = self._steps[-1, 0] + timestep
        self._steps = np.vstack([self._steps, np.empty((alloc_block_size, 5))])
        self._steps[-alloc_block_size:,
                    0] = np.arange(next_time, next_time+timestep*alloc_block_size, timestep)

    def trim(self):
        self._steps = self._steps[:self._act_size]


path: PathArray = PathArray()


def main() -> int:
    global GCode_filename

    if (not GCode_filename):
        GCode_filename = askopenfilename(initialdir=default_folder)

    # Default feedrate set to 2000 mm/min for now
    printer: Printer = Printer(2000)

    startTime: float = time.time()
    with open(GCode_filename, "r") as gcode:
        for line in (l.removesuffix('\n') for l in gcode):
            printer.parse_line(line)

    # Trim array to actual size
    path.trim()
    print("time:", time.time()-startTime)
    print("Total lines:", path._act_size)
    print("Not implemented:")
    for k, v in printer.unimplemented_cmds.items():
        print(f"- {k}: {v}")
    LivePlot3D((200, 200, 200), updater)
    return 0


def updater(frame: int, slider: Slider) -> np.ndarray:
    slider.valmax = path._act_size
    # show a range of values
    return path.get()[slider.val:min(slider.val+500, path._act_size), 1:4]


def inch_to_mm(val: float) -> float:
    return val*25.4


class Printer:
    def __init__(self, default_feedrate: float) -> None:
        self.inch_units: bool = False  # true if in imperial system
        self.relative_move: bool = False  # if movements are relative
        self.relative_e: bool = False  # if Extrusion is relative
        self.feedrate: float = default_feedrate
        self.state: np.ndarray = np.zeros(4)
        self.last_state: np.ndarray = np.zeros(4)
        # offsets used to ensure G92 zeroing can be handled.
        self.workspace_offsets: np.ndarray = np.zeros(4)
        self.unimplemented_cmds: dict[str, int] = {}

    def get_axis_index(self, axis: str) -> int:
        """Converts the axis letter to the index needed for state and offsets"""
        return 'xyze'.index(axis)

    def parse_line(self, line: str):
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
            self.generate_move_steps()
            return
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

    def generate_move_steps(self):
        # feedrate is mm/min -> convert to time
        # dist/feedrate = time
        travel = self.state[:3] - self.last_state[:3]
        dist = np.linalg.norm(travel)
        # Feedrate in mm/min, so convert from min->millisec
        if (self.feedrate == 0):
            raise ValueError("Feedrate cannot be zero")
        travel_time = dist/self.feedrate*60*1000
        num_steps = int(np.ceil(travel_time/timestep))

        # build array
        # interpolate between the two positions
        path.append(np.linspace(
            self.last_state, self.state, num_steps, endpoint=False))

    def generate_dwell_steps(self, cmds: list[str]):
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
        path.append(self.state.reshape(1, 4).repeat(num_steps, axis=0))

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
                i = self.get_axis_index(axis)
                if (self.relative_move):
                    val += self.state[i]
                else:
                    val += self.workspace_offsets[i]
                self.state[i] = val
            elif (axis == 'e'):
                if (self.relative_e):
                    val += self.state[3]
                else:
                    val += self.workspace_offsets[3]
                self.state[3] = val
            elif (axis == 'f'):
                self.feedrate = val

    def updateOffsets(self, cmds: list[str]) -> None:
        """G92 Allows specifying the current position in relation to a newly defined coordinate system, offset from the machine coords. The offsets in XYZE for this coodinate space are stored."""
        for cmd in cmds:
            axis = cmd[0].lower()
            if (axis not in "xyze"):
                continue
            new_val = float(cmd[1:])
            if (self.inch_units):
                new_val = inch_to_mm(new_val)
            i = self.get_axis_index(axis)
            curr_pos = self.state[i]
            # Setting new offset.
            # new_val is the position the Gcode specifies it should be currently, so the offset is calculated to do this. curr_pos is always in absolute machine coords, in mm.
            self.workspace_offsets[i] = curr_pos - new_val


if __name__ == "__main__":
    exit(main())
