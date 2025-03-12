import math
import numpy as np
from matplotlib import pyplot as plt
import GcodeToPath
from LivePlotting import LivePlot2D

# constants
hz = 1000/GcodeToPath.timestep  # sample rate (1/s)
v_max = GcodeToPath.max_velocity  # in mm/s
acc: float = GcodeToPath.acceleration  # m/s^2


def acc_spline(dist: float, vi: float, vf: float) -> tuple[np.ndarray, float]:
    """A 1D interpolation between the start/end positions and velocities with constant acceleration and deceleration.\n
    dist, vi, and vf must be positive. vi and vf must be < max_vel. \n
    Returns the interpolated array and the achieved final velocity (might be lower than target end velocity)"""

    # max velocity you could accelerate too, ignoring max_vel
    act_vm = np.sqrt(acc*dist + .5*(vi**2 + vf**2))

    if (act_vm < vf):  # we cannot accelerate enough to hit vf
        # print("acc only")
        tf = np.sqrt(2*dist/acc)
        ct = math.ceil(tf*hz)
        s_vec = np.linspace(0, tf, ct+1)  # Generate timesteps
        s_vec = .5*acc*np.power(s_vec, 2)
        return s_vec, vi + acc*tf  # vf_act will be < vf

    if (act_vm < vi):  # when vi is higher then vf and we cannot decelerate enough to reach vf
        # print("Deacc only")
        tf = (vi - np.sqrt(vi*vi - 2*acc*dist))/acc
        ct = math.ceil(tf*hz)
        s_vec = np.linspace(0, tf, ct+1)  # Generate timesteps
        s_vec = vi*s_vec - .5*acc*np.power(s_vec, 2)
        return s_vec, vi - acc*tf  # we do not reach vf, the act_vf will be > vf

    if (act_vm <= v_max):  # if we accelerate as much as possible, we will still be below v_max
        # print("acc/deacc")
        t_acc = (act_vm-vi)/acc
        t_deacc = -(vf-act_vm)/acc
        tf = t_acc+t_deacc
        ct = math.ceil(tf*hz)+1
        # index of max velocity, where it switches from acc to deacc
        ct_vm = math.ceil(t_acc*hz)
        s_vec = np.arange(0, ct)/hz
    
        def s_acc(t): return vi*t+0.5*acc*np.power(t, 2)
        def s_deacc(t): return dist + vf *(t-tf) - .5*acc*np.power(t-tf, 2)

        s_vec[0:ct_vm] = s_acc(s_vec[0:ct_vm]) # acceleration portion
        s_vec[ct_vm:] = s_deacc(s_vec[ct_vm:]) # deceleration portion
        return s_vec, vf
    else:
        # print("constant vel section")
        def s_acc(t): return vi*t+0.5*acc*np.power(t, 2)
        def s_deacc(t): return dist + vf *(t) - .5*acc*np.power(t, 2)

        t_acc = (v_max-vi)/acc
        ct_acc = math.ceil(t_acc*hz)+1
        acc_vec = np.arange(0, ct_acc)/hz
        acc_vec = s_acc(acc_vec)

        t_deacc = -(vf-v_max)/acc
        ct_deacc = math.ceil(t_deacc*hz)
        deacc_vec = np.arange(-ct_deacc,1)/hz
        deacc_vec = s_deacc(deacc_vec)

        cv_dist = deacc_vec[0] - acc_vec[-1]
        cv_ct = math.ceil(cv_dist/v_max*hz)
        cv_vec = np.linspace(
            acc_vec[-1], deacc_vec[0], cv_ct, endpoint=False)[1:]

        return np.concatenate([acc_vec, cv_vec, deacc_vec]), vf


def _update(frame: int, slider):
    accel, end_vel = acc_spline(slider.val, 300, 100)

    length = len(accel)
    t = np.arange(0, length/1000, 1/1000)
    return np.vstack([t, accel]), False, False  # (0,.1), (0,52)


if __name__ == "__main__":

    LivePlot2D((0, 100), _update, 4, marker='.')  # type: ignore
