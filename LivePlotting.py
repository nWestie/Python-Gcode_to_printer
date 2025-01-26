import numpy as np
from typing import Callable

from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Line3D
from matplotlib.axes import Axes
from matplotlib import lines

# pyplot.style.use('dark_background')


class LivePlot3D:

    def __init__(self, size: tuple[int, int, int], data_source_func: Callable[[int, Slider], np.ndarray]):
        """size is the max value of each axis of the plot, data_source_func is a function called every frame, which should update and return the data to be displayed, a list of XYZ coordinates"""
        fig = plt.figure()
        ax: Axes = fig.add_subplot(projection='3d')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')  # type: ignore

        ax.axis('square')
        ax.set_xlim(0, size[0])
        ax.set_ylim(0, size[1])
        ax.set_zlim(0, size[2])  # type: ignore
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
        # attempt to animate at 24 fps
        animation = FuncAnimation(
            fig, self.update, frames=50, interval=int(1000/24))

        plt.show()

    def update(self, frame: int) -> tuple[Line3D]:
        self.slider_ax.set_ylim(self.slider.valmin, self.slider.valmax)
        data = self._data_source(frame, self.slider)
        self.line.set_data_3d(data.T)
        return (self.line,)


class LivePlot2D:

    def __init__(self, sl_range: tuple[float, float], data_source_func: Callable[[int, Slider], tuple[np.ndarray, tuple[int, int], tuple[int, int]]], fps_targ=20, col='g', marker=''):
        """size is the max value of each axis of the plot, data_source_func is called every frame and shoul return a [2, N] list of XY coordinates as well as the plot x and y bounds as tuples"""
        fig = plt.figure()
        self._ax: Axes = fig.add_subplot()
        self._ax.set_xlabel('X')
        self._ax.set_ylabel('Y')

        # self._ax.axis('square')
        self._ax.margins(tight=True)
        # self.slider_ax = plt.axes(facecolor="red")
        self.slider_ax = plt.axes((0.05, 0.2, 0.02, 0.65))
        self.slider = Slider(self.slider_ax, 'coarse', sl_range[0], sl_range[1],
                             valinit=float(np.average(sl_range)), orientation='vertical')

        self._source_func = data_source_func
        data, xb, yb = self._source_func(0, self.slider)

        self._line = self._ax.plot(data[0], data[1], color=col, marker=marker)[0]

        # attempt to animate at 24 fps
        animation = FuncAnimation(
            fig, self.update, frames=50, interval=int(1000/fps_targ))

        self._ax.set_xlim(xb)
        self._ax.set_ylim(yb)
        plt.show()

    def update(self, frame: int):
        self.slider_ax.set_ylim(self.slider.valmin, self.slider.valmax)
        data, xb, yb = self._source_func(frame, self.slider)
        self._line.set_xdata(data[0])
        self._line.set_ydata(data[1])
        if(xb):
            self._ax.set_xlim(xb)
        if(yb):
            self._ax.set_ylim(yb)
        return self._line,


def updateData(frame: int, slider: Slider):
    global graphData
    graphData[1] = np.sin(graphData[0]*slider.val)*40
    
    x_bound = np.min(graphData[0])-1, np.max(graphData[0])+1
    y_bound = np.min(graphData[1])-10, np.max(graphData[1])+10
    return graphData, x_bound, y_bound


if __name__ == "__main__":

    resolution = 2000

    graphData = np.empty((2, resolution))
    graphData[0] = np.linspace(0, 200, len(graphData[0]))
    graphData[1] = np.sin(graphData[0])*50

    p = LivePlot2D((0, 2), updateData)
