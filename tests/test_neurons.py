import unittest
import numpy as np
from event_mpc.neurons import INITIAL_NEURONS, NeuronParameters, neuron_rhs, simulate_neurons


class NeuronTests(unittest.TestCase):
    def test_formula_and_state_order(self):
        p=NeuronParameters(); y=INITIAL_NEURONS
        d=neuron_rhs(0,y)
        syn=-1/(1+np.exp(-2*(y[4]+1)))
        expected=(-y[0]+2*np.tanh(y[1]+.9)-1.5*np.tanh(y[2]+.9)+syn-1)/p.tau_fast
        self.assertAlmostEqual(d[0],expected)
        self.assertAlmostEqual(d[4],(-y[4]+y[3])/p.tau_slow)

    def test_exchange_symmetry(self):
        swapped=np.r_[INITIAL_NEURONS[3:],INITIAL_NEURONS[:3]]
        d=neuron_rhs(0,INITIAL_NEURONS)
        np.testing.assert_allclose(neuron_rhs(0,swapped),np.r_[d[3:],d[:3]])

    def test_rhythm_and_refinement(self):
        a=simulate_neurons(.3)
        b=simulate_neurons(.3,rtol=1e-10,atol=1e-12,max_step=43.6575e-6)
        self.assertTrue(a.success and b.success)
        self.assertGreaterEqual(len(a.t_events[0]),10)
        np.testing.assert_allclose(a.t_events[0],b.t_events[0],atol=1e-7,rtol=0)
        upward=a.t_events[0][[neuron_rhs(t,a.sol(t))[0]>0 for t in a.t_events[0]]]
        self.assertGreaterEqual(len(upward),5)
        np.testing.assert_allclose(np.diff(upward)[-3:],.05,atol=2e-4,rtol=0)


if __name__=='__main__':
    unittest.main()
