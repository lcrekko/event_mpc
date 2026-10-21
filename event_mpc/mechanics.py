"""Mirror mechanics: manuscript pp. 2–3, equations (1)–(4).

Equation (2) uses sin(alpha). Equation (4) is retained verbatim as a
separate diagnostic; it is not substituted for the mechanical dynamics.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class MechanicalParameters:
    inertia: float = 1e-7
    natural_frequency: float = 9.9
    damping_ratio: float = 0.01
    kappa: float = 0.030854
    current_limit: float = 0.12
    angle_limit: float = np.deg2rad(10.0)

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError("Mechanical parameters must be finite and positive")

    @property
    def stiffness(self):
        """Equation (25), avoiding rounded table stiffness."""
        return self.inertia * (2 * np.pi * self.natural_frequency) ** 2

    @property
    def damping(self):
        return 2 * self.damping_ratio * self.inertia * 2 * np.pi * self.natural_frequency


@dataclass(frozen=True)
class SolverSettings:
    # RK45 is an explicit implementation choice, not a claim of exact paper RK4.
    rtol: float = 1e-9
    atol: tuple = (1e-11, 1e-9, 1e-16, 1e-16, 1e-16)
    max_step: float = 87.315e-6

    def __post_init__(self):
        if (not np.isfinite(self.rtol) or self.rtol <= 0
                or not np.isfinite(self.max_step) or self.max_step <= 0
                or len(self.atol) != 5
                or any(not np.isfinite(v) or v <= 0 for v in self.atol)):
            raise ValueError("Positive finite solver settings and five absolute tolerances required")


def torque(alpha, current, p):
    """Equation (2), radians and amperes; algebraically even in current."""
    return -p.kappa * np.sin(alpha) * np.asarray(current) ** 2


def energy(alpha, omega, p):
    """Equation (3), joules."""
    return 0.5 * (p.inertia * np.asarray(omega)**2 + p.stiffness * np.asarray(alpha)**2)


def paper_energy_rate(alpha, omega, current, p):
    """Equation (4), unchanged; do not use this to evolve equation (3)."""
    return -p.damping * np.asarray(omega)**2 - p.kappa * np.asarray(current)**2 * alpha * omega


def rhs(t, y, current, p):
    """[alpha, omega, signed exact work, signed Eq.4 work, dissipation]."""
    alpha, omega = y[:2]
    tau = torque(alpha, current, p)
    return np.array([omega, (tau-p.damping*omega-p.stiffness*alpha)/p.inertia,
                     tau*omega, -p.kappa*current**2*alpha*omega,
                     p.damping*omega**2])


@dataclass
class MechanicalRun:
    time: np.ndarray
    state: np.ndarray
    current: np.ndarray
    zero_times: np.ndarray
    turning_times: np.ndarray
    turning_angles: np.ndarray
    status: str
    message: str
    nfev: int


def simulate(initial, segments, p=None, settings=None):
    """Integrate prescribed constant-current segments (end_time, current).

    Segment times are absolute seconds starting at 0. Each switch restarts
    integration while retaining all states. No neuron, sensing or MPC exists.
    Samples are adaptive solver nodes, with switch currents right-continuous.
    """
    p = p or MechanicalParameters()
    settings = settings or SolverSettings()
    initial = np.asarray(initial, dtype=float)
    if initial.shape != (2,) or not np.all(np.isfinite(initial)):
        raise ValueError("Initial state must be finite [alpha, omega]")
    if abs(initial[0]) >= p.angle_limit:
        raise ValueError("Initial angle must be strictly inside operating limits")
    segments = np.asarray(segments, dtype=float)
    if (segments.ndim != 2 or segments.shape[1] != 2 or len(segments) == 0
            or not np.all(np.isfinite(segments))
            or np.any(np.diff(np.r_[0., segments[:, 0]]) <= 0)
            or np.any(segments[:, 1] < 0) or np.any(segments[:, 1] > p.current_limit)):
        raise ValueError("Require increasing positive segment ends and currents in [0, Imax]")

    def zero(t, y):
        return y[0]

    def turning(t, y):
        return y[1]

    def limit(t, y):
        return p.angle_limit - abs(y[0])
    limit.terminal = True
    limit.direction = -1

    y = np.r_[initial, 0., 0., 0.]
    ts, ys, currents, zeros, turns, angles = [], [], [], [], [], []
    start, nfev, status, message = 0., 0, "completed", "Reached prescribed final time"
    for end, current in segments:
        sol = solve_ivp(lambda t, state: rhs(t, state, current, p), (start, end), y,
                        method="RK45", rtol=settings.rtol, atol=settings.atol,
                        max_step=settings.max_step, events=(zero, turning, limit))
        nfev += sol.nfev
        # Replace the old segment endpoint: no duplicate sample or state reset.
        if ts:
            ts[-1] = ts[-1][:-1]
            ys[-1] = ys[-1][:, :-1]
            currents[-1] = currents[-1][:-1]
        ts.append(sol.t); ys.append(sol.y)
        currents.append(np.full(len(sol.t), current))
        for t, state in zip(sol.t_events[0], sol.y_events[0]):
            if t > 1e-12 and abs(state[1]) > 1e-10 and (not zeros or t-zeros[-1] > 1e-10):
                zeros.append(t)
        for t, state in zip(sol.t_events[1], sol.y_events[1]):
            acceleration = rhs(t, state, current, p)[1]
            if (t > 1e-12 and abs(acceleration) > 1e-10
                    and (not turns or t-turns[-1] > 1e-10)):
                turns.append(t); angles.append(state[0])
        if not sol.success:
            status, message = "integration_failed", sol.message
            break
        if len(sol.t_events[2]):
            status, message = "angle_limit", "Reached maximum allowable mirror angle"
            break
        start, y = end, sol.y[:, -1]
    return MechanicalRun(np.concatenate(ts), np.concatenate(ys, axis=1),
                         np.concatenate(currents), np.asarray(zeros), np.asarray(turns),
                         np.asarray(angles), status, message, nfev)


def analytical_unforced(time, initial, p):
    """Independent underdamped closed-form solution of equation (1), I=0."""
    if p.damping_ratio >= 1:
        raise ValueError("Analytical reference requires an underdamped system")
    t = np.asarray(time)
    a, w = initial
    rate = p.damping / (2*p.inertia)
    frequency = np.sqrt(p.stiffness/p.inertia-rate**2)
    c = (w+rate*a)/frequency
    u = a*np.cos(frequency*t)+c*np.sin(frequency*t)
    du = -a*frequency*np.sin(frequency*t)+c*frequency*np.cos(frequency*t)
    return np.array([np.exp(-rate*t)*u, np.exp(-rate*t)*(du-rate*u)])
