import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from event_mpc.closed_loop import run_closed_loop
from event_mpc.optimization import SearchSettings,LOWER,UPPER,optimize


class StartupComparisonTests(unittest.TestCase):
    def test_identical_initial_half_swing_then_causal_uniform_update(self):
        theta=[.05,1.5,2.]
        with tempfile.TemporaryDirectory() as tmp:
            fixed=Path(tmp)/'fixed';mpc=Path(tmp)/'mpc'
            a=run_closed_loop(fixed,2,1,SearchSettings(method='fixed'),initial_theta=theta)
            b=run_closed_loop(mpc,2,1,SearchSettings(method='uniform',samples=4),
                              initial_theta=theta,startup_intervals=1)
            self.assertEqual((a['status'],b['status']),('completed','completed'))
            fa=json.loads((fixed/'actions.json').read_text());ma=json.loads((mpc/'actions.json').read_text())
            fe=json.loads((fixed/'events.json').read_text())['events'];me=json.loads((mpc/'events.json').read_text())['events']
            self.assertEqual(fe[0],me[0])
            self.assertTrue(ma[0]['startup']);self.assertFalse(ma[1]['startup'])
            self.assertEqual(ma[0]['theta'],theta)
            self.assertEqual(fa[0]['theta'],fa[1]['theta'])
            self.assertEqual(ma[1]['applied_time'],me[0]['observation']['available_time'])
            self.assertTrue(np.all(np.array(ma[1]['theta'])>=LOWER))
            self.assertTrue(np.all(np.array(ma[1]['theta'])<=UPPER))

    def test_refinement_keeps_its_original_bound_validation(self):
        def evaluate(c):return np.sum(c*c,axis=(1,2)),np.zeros(len(c),int)
        with self.assertRaisesRegex(ValueError,'outside bounds'):
            optimize(evaluate,np.random.default_rng(1),previous_theta=[.05,1.5,2.])

    def test_user_bounds_are_per_search_and_do_not_change_old_defaults(self):
        def evaluate(c):return np.sum(c*c,axis=(1,2)),np.zeros(len(c),int)
        settings=SearchSettings(method='uniform',samples=32,lower=(0.,1.5,1.),upper=(.12,2.5,2.))
        r=optimize(evaluate,np.random.default_rng(1),settings,previous_theta=[.05,1.5,2.])
        draws=r.diagnostics[0]['sequences']
        self.assertTrue(np.all(draws>=settings.lower));self.assertTrue(np.all(draws<=settings.upper))
        self.assertTrue(np.any(draws[:,:,1]>UPPER[1]))
        self.assertTrue(np.any(draws[:,:,2]<LOWER[2]))
        np.testing.assert_array_equal(SearchSettings().lower,LOWER)
        np.testing.assert_array_equal(SearchSettings().upper,UPPER)
