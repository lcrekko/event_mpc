import unittest
from dataclasses import replace
import numpy as np
from event_mpc.mechanics import (MechanicalParameters, SolverSettings, simulate,
                                  analytical_unforced, energy, rhs, torque)
from event_mpc.validation import validate


class MechanicalTests(unittest.TestCase):
    def setUp(self):
        self.p = MechanicalParameters()

    def test_independent_numerical_validation(self):
        report = validate()
        self.assertTrue(report["passed"], report)

    def test_torque_formula_units_and_large_angle(self):
        # Explicit non-small-angle input catches accidental alpha-for-sin substitution.
        self.assertAlmostEqual(torque(np.pi/2, .1, self.p), -.00030854, places=14)
        self.assertEqual(torque(.1, 0., self.p), 0.)

    def test_switch_continuity_against_unforced_reference(self):
        run = simulate([.05, 1.], [(.01, 0.), (.02, 0.), (.03, 0.)])
        expected = analytical_unforced(run.time, [.05, 1.], self.p)
        np.testing.assert_allclose(run.state[:2], expected, atol=1e-9, rtol=1e-8)
        self.assertTrue(np.all(np.diff(run.time) > 0))
        self.assertEqual(np.count_nonzero(run.time == .01), 1)
        self.assertEqual(np.count_nonzero(run.time == .02), 1)

    def test_nonzero_current_switch_preserves_all_continuation_states(self):
        full = simulate([0., 5.5137], [(.02,.03),(.04,.08)])
        first = simulate([0., 5.5137], [(.02,.03)])
        at_switch = np.flatnonzero(full.time == .02)
        self.assertEqual(len(at_switch), 1)
        np.testing.assert_array_equal(full.state[:,at_switch[0]], first.state[:,-1])
        self.assertEqual(full.current[at_switch[0]], .08)

    def test_operating_limit_stops_and_reports(self):
        run = simulate([0., 30.], [(.1, 0.)])
        self.assertEqual(run.status, "angle_limit")
        self.assertLess(run.time[-1], .1)
        self.assertAlmostEqual(abs(run.state[0,-1]), self.p.angle_limit, places=12)

    def test_invalid_inputs_rejected(self):
        for segments in ([], [(0.,.01)], [(.1,-.01)], [(.1,.13)],
                         [(.1,0.),(.05,0.)], [(np.nan,0.)]):
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                simulate([0.,1.], segments)
        for initial in ([0.], [np.nan,1.], [self.p.angle_limit,0.]):
            with self.assertRaises(ValueError):
                simulate(initial, [(.1,0.)])
        with self.assertRaises(ValueError):
            replace(self.p, inertia=-1)
        with self.assertRaises(ValueError):
            SolverSettings(max_step=0.)

    def test_quiescent_state_has_no_transverse_events(self):
        run = simulate([0.,0.], [(.001,0.)])
        self.assertEqual(run.status, "completed")
        np.testing.assert_array_equal(run.state, 0.)
        self.assertEqual(len(run.zero_times), 0)
        # Stationary omega=0 is not an isolated turning point.
        self.assertEqual(len(run.turning_times), 0)

    def test_energy_derivative_by_finite_difference(self):
        # Independent directional derivative of Eq. (3), not the integrated auxiliary.
        a,w,i = .08,-1.3,.09
        d = rhs(0.,[a,w,0.,0.,0.],i,self.p)
        h = 1e-7
        measured = (energy(a+h*d[0],w+h*d[1],self.p)
                    -energy(a-h*d[0],w-h*d[1],self.p))/(2*h)
        expected = -self.p.damping*w*w+torque(a,i,self.p)*w
        self.assertAlmostEqual(measured, expected, delta=1e-14)


if __name__ == "__main__":
    unittest.main()
