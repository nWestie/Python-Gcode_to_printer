import numpy as np
from typing import Callable

from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Line3D
from matplotlib.axes import Axes

# pyplot.style.use('dark_background')


class LivePlot3D:

    def __init__(self, size: tuple[int, int, int], data_source_func: Callable[[int, Slider], np.ndarray]):
        """size is the max value of each axis of the plot, data_source_func is a function called every frame, which should update and return the data to be displayed, a list of XYZ coordinates"""
        fig = plt.figure()
        ax: Axes = fig.add_subplot(projection='3d')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        ax.axis('square')
        ax.set_xlim(0, size[0])
        ax.set_ylim(0, size[1])
        ax.set_zlim(0, size[2])
        ax.margins(tight=True)
        # self.slider_ax = plt.axes(facecolor="red")
        self.slider_ax = plt.axes((0.05, 0.2, 0.02, 0.65), facecolor="red")
        self.slider = Slider(self.slider_ax, 'coarse', 1, 20,
                             valinit=1, valstep=1, orientation='vertical')

        self.lines = []
        self._data_source = data_source_func
        data = self._data_source(0, self.slider)
        self.line = Line3D(data[:, 0], data[:, 1],
                           data[:, 2], c='g', marker='.', linewidth=1)
        ax.add_artist(self.line)
        animation = FuncAnimation(fig, self.update, frames=50, interval=50)

        plt.show()

    def update(self, frame: int) -> tuple[Line3D]:
        self.slider_ax.set_ylim(self.slider.valmin, self.slider.valmax)
        data = self._data_source(frame, self.slider)
        self.line.set_data_3d(data.T)
        return self.line,


def updateData(frame: int, slider: Slider):
    global graphData
    slider.valmax = len(graphData)
    return graphData[:int(slider.val)]


if __name__ == "__main__":
    resolution = 2000

    graphData = np.empty((resolution, 3))
    graphData[:, 0] = np.linspace(0, 100, len(graphData))
    x = graphData[:, 0]
    t = x/100*5*2*np.pi
    graphData[:, 1] = np.sin(t)*40+50
    graphData[:, 2] = np.cos(t)*40+50

    p = LivePlot3D((100, 100, 100), updateData)
