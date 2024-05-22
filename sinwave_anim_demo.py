import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.1, bottom=0.25)  # Adjust the subplot to make room for the slider

# Initial values
t = np.linspace(0, 10, 1000)
a0 = 1  # Initial amplitude
f0 = 1  # Initial frequency
s = a0 * np.sin(2 * np.pi * f0 * t)
[line] = ax.plot(t, s)

# Adjust the main plot to make room for the sliders
ax.margins(x=0)

# Add sliders for amplitude and frequency
axcolor = 'lightgoldenrodyellow'
ax_amp = plt.axes([0.1, 0.1, 0.65, 0.03], facecolor="red")
ax_freq = plt.axes([0.1, 0.15, 0.65, 0.03], facecolor="blue")

# Define the sliders
slider_amp = Slider(ax_amp, 'Amplitude', 0.1, 10.0, valinit=a0)
slider_freq = Slider(ax_freq, 'Frequency', 0.1, 10.0, valinit=f0)

# Update function to be called when the slider's value changes
def update(val):
    amp = slider_amp.val
    freq = slider_freq.val
    line.set_ydata(amp * np.sin(2 * np.pi * freq * t))
    fig.canvas.draw_idle()  # Redraw the figure to update the plot

# Register the update function with each slider
slider_amp.on_changed(update)
slider_freq.on_changed(update)

# Display the plot
plt.show()
