import os
import sys
from tkinter.filedialog import askopenfile


host_folder = os.path.dirname(os.path.abspath(sys.argv[0]))
with open(host_folder+"/touched it.txt", 'w') as file:
    file.write("HIIIII\n")
    for arg in sys.argv:
        file.write(f"{arg}\n")
    file.write("END ARGS\nENV VARS:\n")
    for key, value in os.environ.items():
        file.write(f"{key}: {value}\n")





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
