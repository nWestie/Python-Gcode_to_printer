import math
import numpy as np
from matplotlib import pyplot as plt
import GcodeToPath
from LivePlotting import LivePlot2D

# constants
hz = 1000/GcodeToPath.timestep  # sample rate (1/s)
max_vel = GcodeToPath.max_velocity  # in mm/s
acc: float = GcodeToPath.acceleration  # m/s^2

time_til_max_vel = max_vel/acc
time = np.arange(0, time_til_max_vel+1/hz, 1/hz)
# the acceleration/deceleration curves from 0m/s to the max velocity.
acc_curve = 1/2*acc*np.square(time)  # starts at 0
deacc_curve = - np.flip(acc_curve)  # ends at 0
del (time)


def acc_spline(dist: float, vi: float, vf: float) -> tuple[np.ndarray, float]:
    """A 1D interpolation between the start/end positions and velocities with constant acceleration and deceleration.\n
    dist, vi, and vf must be positive. vi and vf must be < max_vel. \n
    Returns the interpolated array and the achieved final velocity (might be lower than target end velocity)"""

    # get acc portion based on inital velocity
    acc_start_ct = round(vi/acc*hz)
    s_acc = acc_curve[acc_start_ct:].copy()
    s_acc -= s_acc[0]  # shift acc to start at 0

    deacc_end_ct = round(vf/acc*hz)
    s_deacc = deacc_curve[:-deacc_end_ct].copy()\
        if deacc_end_ct > 0 else deacc_curve
    s_deacc -= s_deacc[-1] - dist  # shift deacc to end at dist

    overlap_dist = s_acc[-1] - s_deacc[0]
    # constant velocity portion, if needed
    if (overlap_dist < 0):
        print("linear chunk")
        lin_dist = s_deacc[0]-s_acc[-1]
        lin_ct = round(lin_dist/(max_vel/hz)) + 1
        cv_points = np.linspace(s_acc[-1], s_deacc[0], lin_ct, endpoint=False)
        cv_points = cv_points[1:]
        return np.concatenate((s_acc, cv_points, s_deacc)), vf
    # else, means dist is not long enough to need a constant velocity section

    # if we trim off the end of the acc curve and start of the deacc curve symmetrically,
    # their end/start velocities respectively will match
    t_overlap = (max_vel-np.sqrt(max_vel*max_vel-acc*overlap_dist))/acc
    # num of samples trimmed from EACH side(acc/deacc):
    ct_overlap = int(np.ceil(t_overlap*hz))

    if ct_overlap < min(len(s_acc), len(s_deacc)):
        # Accelerate/decelerate, but don't hit max_vel
        s_acc = s_acc[:-ct_overlap]
        s_deacc = s_deacc[ct_overlap:]
        print(f"acc/deacc: max_vel = {vi+acc*len(s_acc)/hz}")
        return np.concatenate((s_acc, s_deacc)), vf

    if vf > vi:
        # Only accelerate, will undershoot vf
        print("accel only")
        t_keep = (-vi + np.sqrt(vi*vi+2*acc*dist))/acc
        final_vel: float = vi + acc*t_keep
        return s_acc[:int(t_keep*hz)+1], final_vel
    else:
        # Only decelerate, will overshoot vf
        print("WARN: overshot vf")
        # Start at velocity vi, and decelerate for dist
        deacc_start_ct = round((max_vel-vi)/acc*hz)
        t_keep = (+vi - np.sqrt(vi*vi-2*acc*dist))/acc
        end_vel = vi - acc*t_keep
        s_deacc = deacc_curve[deacc_start_ct:deacc_start_ct +
                              round(t_keep*hz)+1].copy()
        return s_deacc-s_deacc[0], end_vel


def _update(frame: int, slider):
    accel, end_vel = acc_spline(
        10, slider.val, 300)

    # print(accel[-1])
    # print(end_vel)
    # print((accel[-1]-accel[-2])*hz)
    length = len(accel)
    t= np.arange(0, length/1000, 1/1000)
    return np.vstack([t, accel]), (0,.05), (0,12)


if __name__ == "__main__":

    LivePlot2D((100, 500), _update, 5, marker='o')
