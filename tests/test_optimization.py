import unittest
import numpy as np
from event_mpc.optimization import optimize,SearchSettings,shifted,LOWER,UPPER
from event_mpc.objective import Objective
from event_mpc.prediction import Prediction


class OptimizationTests(unittest.TestCase):
    def test_literal_timing_index_and_work(self):
        obj=Objective();a=obj.amplitude
        r=Prediction('completed',[.001,.052,10.],[a,-a],[1e-7,2e-7])
        expected=.001**2+.002**2+obj.array()[3]*3e-7
        self.assertAlmostEqual(obj.evaluate(r,0),expected)
        r.times[-1]=1000
        self.assertAlmostEqual(obj.evaluate(r,0),expected)  # No terminal-time penalty.

    def test_weighted_mean_and_best_valid(self):
        target=np.array([.04,2.,1.5])
        def evaluate(c):return np.sum((c-target)**2,axis=(1,2)),np.zeros(len(c),int)
        r=optimize(evaluate,np.random.default_rng(1),SearchSettings(samples=8,rounds=2))
        self.assertFalse(r.fallback)
        allcosts=np.concatenate([d['costs'] for d in r.diagnostics])
        self.assertEqual(r.cost,np.min(allcosts))
        self.assertEqual(len(r.diagnostics),4)
        for d in r.diagnostics:
            self.assertTrue(np.all(d['sequences']>=LOWER));self.assertTrue(np.all(d['sequences']<=UPPER))
        first=r.diagnostics[0];w=np.exp(-(first['costs']-min(first['costs']))/250e-6);w/=sum(w)
        np.testing.assert_allclose(r.diagnostics[1]['sequences'][0],np.sum(w[:,None,None]*first['sequences'],axis=0))

    def test_invalid_fallback_and_shift(self):
        def invalid(c):return np.full(len(c),np.inf),np.ones(len(c),int)
        r=optimize(invalid,np.random.default_rng(3),SearchSettings(samples=4),previous_theta=[.05,2.1,1.6])
        self.assertTrue(r.fallback)
        np.testing.assert_array_equal(r.sequence,np.tile([0.,2.1,1.6],(4,1)))
        x=np.arange(12).reshape(4,3);np.testing.assert_array_equal(shifted(x),np.vstack([x[1:],x[-1]]))

    def test_uniform_and_constant_parameter_options(self):
        def evaluate(c):return np.sum(c**2,axis=(1,2)),np.zeros(len(c),int)
        r=optimize(evaluate,np.random.default_rng(1),SearchSettings(samples=5,method='uniform',constant_parameters=True))
        self.assertEqual(len(r.diagnostics),1)
        for c in r.diagnostics[0]['sequences']:np.testing.assert_array_equal(c,np.tile(c[0],(4,1)))
