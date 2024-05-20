import numpy as np
from dataclasses import dataclass
from tkinter.filedialog import askopenfilename

GCode_filename = "./gcode/testing.gcode5"
# GCode_filename = "C:/Users/westn/Documents/code/DualStagePrinting/1- Cube.gcode"
default_folder = "./gcode"


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

    def copy(self):
        return PrinterPos(self.x, self.y, self.z, self.e, self.feedrate)


class Printer:
    inch_units: bool = False  # true if in imperial system
    relative_move: bool = False  # if movements are relative
    relative_e: bool = False  # if Extrusion is relative
    # current_pos: PrinterPos
    last_pos: PrinterPos = PrinterPos(0, 0, 0, 0, 0)

    def parse_line(self, line: str) -> PrinterPos:
        # Remove comments(everything after a semicolon)
        line = line.split(";")[0]
        if (not line):
            return self.last_pos

        cmds = [x for x in line.split(' ') if len(x)]
        cmd = cmds[0].upper()
        if (cmd in ('G0', 'G1')):  # Basic movement
            return self.parse_movement(cmds)
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
        elif (cmd in ('G4', 'M0', 'M1')):  # Dwell
            # https://marlinfw.org/docs/gcode/M000-M001.html
            print("#TODO: Dwell not implemented")
        elif (cmd == 'G29'):
            # https://marlinfw.org/docs/gcode/G029-abl-3point.html
            print("#TODO: Homing not implemented")
        elif (cmd == 'G92'):
            # https://marlinfw.org/docs/gcode/G092.html
            print("#TODO: Set Position not implemented")
        elif (cmd in ('M104', 'M140', 'M141', 'M190', 'M109', 'M191')):
            print(f"Temperature control not handled({cmd})")
        else:
            print(f"{cmd} not currently implemented")

    def parse_movement(self, cmds: list[str]) -> PrinterPos:
        """Return an updated position based on the movements specified"""
        new_state: PrinterPos = self.last_pos.copy()
        for cmd in cmds:
            axis = cmd[0].lower()
            val = float(cmd[1:])
            if (axis in 'xyz'):
                if (self.inch_units):
                    val = inch_to_mm(val)
                if (self.relative_move):
                    val += getattr(new_state, axis)
                setattr(new_state, axis, val)
            elif (axis == 'e'):
                if (self.inch_units):
                    val = inch_to_mm(val)
                if (self.relative_e):
                    val += new_state.e
                new_state.e = val
            elif (axis == 'f'):
                new_state.feedrate = val
        return new_state


def main() -> int:
    global GCode_filename
    if (not GCode_filename):
        GCode_filename = askopenfilename(initialdir=default_folder)
    printer: Printer = Printer()
    with open(GCode_filename, "r") as gcode:
        for line in gcode:
            print(line, end='')
            new_state = printer.parse_line(line)
            print(new_state)
            last_state = new_state


allCommands = set()


if __name__ == "__main__":
    exit(main())
