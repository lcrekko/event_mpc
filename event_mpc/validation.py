"""Independent numerical checks with predeclared tolerances (docs/milestone-a.md)."""
from dataclasses import replace
import numpy as np
from .mechanics import (MechanicalParameters, SolverSettings, simulate,
                        analytical_unforced, torque, rhs, energy, paper_energy_rate)
from .metrics import mechanical_metrics


def validate():
    p = MechanicalParameters()
    initial = [0., 5.5137]
    checks = []

    def check(name, value, bound):
        checks.append(dict(name=name, value=float(value), maximum=float(bound),
                           passed=bool(np.isfinite(value) and value <= bound)))

    free = simulate(initial, [(0.3, 0.)], p)
    reference = analytical_unforced(free.time, initial, p)
    check("free_angle_error_rad", np.max(abs(reference[0]-free.state[0])), 1e-8)
    check("free_speed_error_rad_per_s", np.max(abs(reference[1]-free.state[1])), 1e-6)
    wd = 2*np.pi*p.natural_frequency*np.sqrt(1-p.damping_ratio**2)
    target = np.arange(1, len(free.zero_times)+1)*np.pi/wd
    check("free_crossing_error_s", np.max(abs(target-free.zero_times)), 1e-8)
    check("free_energy_increase_J", max(0., np.max(np.diff(energy(*free.state[:2], p)))), 1e-14)
    check("free_status_and_event_count", int(free.status != "completed" or len(free.zero_times) != 5), 0)

    forced = simulate(initial, [(0.025, .12), (.050, 0.), (.075, .12), (.15, 0.)], p)
    m = mechanical_metrics(forced.state, p)
    check("forced_exact_energy_relative_residual", m["exact_balance_relative_residual"], 1e-7)
    check("forced_completed", int(forced.status != "completed"), 0)
    # Check the published equation as an algebraic diagnostic, not a false balance identity.
    a, w, current = .1, -2., .12
    derivative = rhs(0, [a,w,0,0,0], current, p)
    energy_derivative = p.inertia*w*derivative[1]+p.stiffness*a*w
    difference = energy_derivative-paper_energy_rate(a,w,current,p)
    expected = p.kappa*current**2*(a-np.sin(a))*w
    check("equation_4_difference_identity_W", abs(difference-expected), 1e-18)
    check("torque_restoring_and_current_even", int(not (
        torque(a,current,p) < 0 < torque(-a,current,p)
        and torque(a,current,p) == torque(a,-current,p))), 0)

    refined = simulate(initial, [(0.025,.12),(.050,0.),(.075,.12),(.15,0.)], p,
                       replace(SolverSettings(), rtol=1e-11,
                               atol=(1e-13,1e-11,1e-18,1e-18,1e-18), max_step=43.6575e-6))
    if len(forced.zero_times) != len(refined.zero_times) or not len(forced.zero_times):
        check("refined_crossing_count", 1, 0)
    else:
        check("refined_crossing_difference_s", np.max(abs(forced.zero_times-refined.zero_times)), 1e-7)
    if len(forced.turning_angles) != len(refined.turning_angles) or not len(forced.turning_angles):
        check("refined_turning_count", 1, 0)
    else:
        check("refined_extremum_difference_rad", np.max(abs(forced.turning_angles-refined.turning_angles)), 1e-7)
    check("refined_final_state_scaled_difference", np.max(abs(
        (forced.state[:2,-1]-refined.state[:2,-1])/np.array([.1,10.]))), 1e-7)
    check("refined_work_difference_J", abs(forced.state[2,-1]-refined.state[2,-1]), 1e-12)
    return {"passed": all(c["passed"] for c in checks), "checks": checks,
            "forced_energy_diagnostics": m,
            "equation_4_note": "Printed equation retained; nonzero balance residual is reported, not hidden."}
