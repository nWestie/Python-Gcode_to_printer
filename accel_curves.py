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

    if (act_vm < vi):
        print("Deacc only")
        t = (vi - np.sqrt(vi**2 - 2*acc*dist))/acc
        ct = math.ceil(t*hz)
        s_vec = np.linspace(0, t, ct+1)  # Generate timesteps
        s_vec = vi*s_vec - .5*acc*np.power(s_vec, 2)
        return s_vec, vi - acc*t
    if (act_vm < vf):
        print("acc only")
        t = np.sqrt(2*dist/acc)
        ct = math.ceil(t*hz)
        s_vec = np.linspace(0, t, ct+1)  # Generate timesteps
        s_vec = .5*acc*np.power(s_vec, 2)
        return s_vec, vi - acc*t

    if (act_vm <= v_max):
        print("acc/deacc")
        t_acc = (act_vm-vi)/acc
        t_deacc = -(vf-act_vm)/acc
        t = t_acc+t_deacc
        ct = math.ceil(t*hz)
        # index of max velocity, where it switches from acc to deacc
        ct_vm = math.ceil(t_acc*hz)+1
        s_vec = np.linspace(0, t, ct+1)
        s_acc = s_vec[0:ct_vm]
        s_deacc = s_vec[ct_vm:]
        s_vec[0:ct_vm] = vi*s_acc+0.5*acc*np.power(s_acc, 2)
        s_vec[ct_vm:] = s_acc[-1] + act_vm * \
            (s_deacc-t_acc) - .5*acc*np.power(s_deacc-t_acc, 2)
        return s_vec, vf
    else:
        print("constant vel section")
        t_acc = (v_max-vi)/acc
        ct_acc = math.ceil(t_acc*hz)
        acc_vec = np.linspace(0, t_acc, ct_acc+1)
        acc_vec = vi*acc_vec + 0.5*acc*np.power(acc_vec, 2)

        t_deacc = -(vf-v_max)/acc
        ct_deacc = math.ceil(t_deacc*hz)
        deacc_vec = np.linspace(0, t_deacc, ct_deacc+1)
        deacc_vec = dist + vf*(deacc_vec-t_deacc) - .5 * \
            acc*np.power(deacc_vec-t_deacc, 2)

        cv_dist = deacc_vec[0] - acc_vec[-1]
        cv_ct = math.ceil(cv_dist/v_max*hz)
        cv_vec = np.linspace(acc_vec[-1], deacc_vec[0], cv_ct+1, endpoint=False)[1:]

        return np.concatenate([acc_vec, cv_vec, deacc_vec]), vf


def _update(frame: int, slider):
    accel, end_vel = acc_spline(slider.val, 300, 100)

    length = len(accel)
    t = np.arange(0, length/1000, 1/1000)
    return np.vstack([t, accel]), False, False # (0,.1), (0,52)


if __name__ == "__main__":

    LivePlot2D((0, 100), _update, 4, marker='.')  # type: ignore
