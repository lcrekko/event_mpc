import unittest
import numpy as np
from event_mpc.coupled import INITIAL_STATE,NOMINAL_THETA
from event_mpc.neurons import NeuronParameters
from event_mpc.mechanics import MechanicalParameters
from event_mpc.prediction import predict
from event_mpc.objective import Objective
from event_mpc.fast_prediction import sequence_prediction,parameter_arrays,batch_cost


class FastPredictionTests(unittest.TestCase):
    def test_backend_against_independent_scipy(self):
        p=MechanicalParameters();n=NeuronParameters();pa,na=parameter_arrays(p,n)
        rng=np.random.default_rng(17)
        for i in range(5):
            seq=(np.tile(NOMINAL_THETA,(4,1))+rng.normal(size=(4,3))*[.003,.01,.01]
                 if i<3 else rng.uniform([0.,1.8,1.3],[.12,2.2,1.7],size=(4,3)))
            reference=predict(INITIAL_STATE,seq,p=p,n=n)
            times,amps,work,states,status=sequence_prediction(INITIAL_STATE,seq,0.,0.,pa,na)
            self.assertEqual(reference.status,'completed');self.assertEqual(status,0)
            np.testing.assert_allclose(times,reference.times,atol=2e-7,rtol=0)
            np.testing.assert_allclose(amps,reference.amplitudes,atol=2e-6,rtol=0)
            np.testing.assert_allclose(work,reference.work,atol=2e-10,rtol=1e-4)
            np.testing.assert_allclose(states,reference.continuation,atol=2e-4,rtol=1e-4)
        costs,statuses=batch_cost(INITIAL_STATE,seq[None],0.,0.,0,pa,na,Objective().array(),87.315e-6,1e-7,.1)
        self.assertEqual(statuses[0],0)
        self.assertAlmostEqual(costs[0],Objective().evaluate(reference,0),delta=2e-8)

    def test_invalid_status_and_refinement(self):
        pa,na=parameter_arrays(MechanicalParameters(),NeuronParameters())
        seq=np.tile(NOMINAL_THETA,(4,1))
        a=sequence_prediction(INITIAL_STATE,seq,0.,0.,pa,na)
        b=sequence_prediction(INITIAL_STATE,seq,0.,0.,pa,na,43.6575e-6,1e-9)
        self.assertEqual(a[-1],0);self.assertEqual(b[-1],0)
        np.testing.assert_allclose(a[0],b[0],atol=2e-7,rtol=0)
        np.testing.assert_allclose(a[1],b[1],atol=2e-6,rtol=0)
        timeout=sequence_prediction(INITIAL_STATE,seq,0.,0.,pa,na,87.315e-6,1e-7,.001)
        self.assertEqual(timeout[-1],1)
