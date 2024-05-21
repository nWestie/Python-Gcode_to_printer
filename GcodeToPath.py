import numpy as np
from dataclasses import dataclass
from tkinter.filedialog import askopenfilename
from matplotlib.widgets import Slider
from typing import Optional
from plotting import LivePlot3D
from time import time

GCode_filename = ""
# GCode_filename = "./gcode/1-Cube.gcode"
# GCode_filename = "./gcode/testing.gcode"
default_folder = "./gcode"

# time to beat: 70sec
# With 1000 row chunked allocations: 0.5sec
# With 5000 row chunked allocations: 0.45sec
# - Calling this good
lineCoords: np.ndarray = np.zeros((0, 3))


def main() -> int:
    global GCode_filename, lineCoords

    if (not GCode_filename):
        GCode_filename = askopenfilename(initialdir=default_folder)
    printer: Printer = Printer()
    i: int = 0
    startTime: float = time()
    with open(GCode_filename, "r") as gcode:
        for line in (l.removesuffix('\n') for l in gcode):
            new_state = printer.parse_line(line)
            if (new_state):
                if (i == len(lineCoords)):
                    lineCoords = np.vstack([lineCoords, np.empty((5000, 3))])
                lineCoords[i] = np.array(
                    [new_state.x, new_state.y, new_state.z])
                i += 1
    lineCoords = lineCoords[:i]
    print("time:", time()-startTime)
    print("Total lines:", i)
    print("Not implemented:")
    for k, v in printer.unimplemented_cmds.items():
        print(f"{k}: {v}")
    LivePlot3D((200, 200, 200), updater)
    return 0


def updater(frame: int, slider: Slider) -> np.ndarray:
    slider.valmax = len(lineCoords)
    return lineCoords[:slider.val]


def inch_to_mm(val: float) -> float:
    return val*25.4


@dataclass
class PrinterPos:
    # Represents moving to this position with the specified feedrate
    # All units are absolute mm
    x: float = 0
    y: float = 0
    z: float = 0
    e: float = 0  # extrusion
    feedrate: float = 0

    def copy(self) -> 'PrinterPos':
        return PrinterPos(self.x, self.y, self.z, self.e, self.feedrate)


class Printer:
    def __init__(self) -> None:
        self.inch_units: bool = False  # true if in imperial system
        self.relative_move: bool = False  # if movements are relative
        self.relative_e: bool = False  # if Extrusion is relative
        # current_pos: PrinterPos
        self.current_pos: PrinterPos = PrinterPos(0, 0, 0, 0, 0)
        # last_pos: PrinterPos = PrinterPos(0, 0, 0, 0, 0)
        # offsets used to ensure G92 zeroing can be handled.
        self.workspace_offsets: dict[str, float] = {
            'x': 0, 'y': 0, 'z': 0, 'e': 0}
        self.unimplemented_cmds: dict[str, int] = {}

    def parse_line(self, line: str) -> Optional[PrinterPos]:
        # Remove comments(everything after a semicolon)
        line = line.split(";")[0]
        if (not line):
            return None

        cmds = [x for x in line.split(' ') if len(x)]
        cmd = cmds[0].upper()
        if (cmd in ('G0', 'G1')):  # Basic movement
            self.parse_movement(cmds)
            # self.last_pos = self.current_pos
            return self.current_pos

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
# Dwell: 'G4', 'M0', 'M1'

    def parse_movement(self, cmds: list[str]) -> None:
        """Called for G0/1. Returns an updated position based on the movements specified"""
        for cmd in cmds:
            # Split command to letter/number
            axis = cmd[0].lower()
            val = float(cmd[1:])
            if (self.inch_units):
                val = inch_to_mm(val)
            if (axis in 'xyz'):
                # Offsets only are required in absolute mode, in relative mode,
                # all commands are offset from the last position,
                # so the workspace offset doesn't matter
                if (self.relative_move):
                    val += getattr(self.current_pos, axis)
                else:
                    val += self.workspace_offsets[axis]
                setattr(self.current_pos, axis, val)
            elif (axis == 'e'):
                if (self.relative_e):
                    val += self.current_pos.e
                else:
                    val += self.workspace_offsets[axis]
                self.current_pos.e = val
            elif (axis == 'f'):
                self.current_pos.feedrate = val

    def updateOffsets(self, cmds: list[str]) -> None:
        """G92 Allows specifying the current position in relation to a newly defined coordinate system, offset from the machine coords. The offsets in XYZE for this coodinate space are stored."""
        for cmd in cmds:
            axis = cmd[0].lower()
            if (axis not in "xyze"):
                continue
            new_val = float(cmd[1:])
            if (self.inch_units):
                new_val = inch_to_mm(new_val)
            curr_pos = getattr(self.current_pos, axis)
            # Setting new offset.
            # new_val is the position the Gcode specifies it should be currently, so the offset is calculated to do this. curr_pos is always in absolute machine coords, in mm.
            self.workspace_offsets[axis] = curr_pos - new_val


def printd(*args):
    print(*args)


if __name__ == "__main__":
    exit(main())
