"""Postprocessing of saved mechanical trajectories; no integration."""
import numpy as np
from .mechanics import energy


def mechanical_metrics(state, p):
    e = energy(state[0], state[1], p)
    change = e-e[0]
    exact_residual = change-state[2]+state[4]
    paper_residual = change-state[3]+state[4]
    scale = max(float(e[0]), np.finfo(float).tiny)
    return {
        "initial_energy_J": float(e[0]),
        "maximum_abs_angle_rad": float(np.max(abs(state[0]))),
        "exact_balance_max_abs_residual_J": float(np.max(abs(exact_residual))),
        "exact_balance_relative_residual": float(np.max(abs(exact_residual))/scale),
        "equation_4_max_abs_residual_J": float(np.max(abs(paper_residual))),
        "equation_4_relative_residual": float(np.max(abs(paper_residual))/scale),
        "signed_exact_work_J": float(state[2, -1]),
        "signed_equation_4_work_J": float(state[3, -1]),
        "dissipated_energy_J": float(state[4, -1]),
    }
