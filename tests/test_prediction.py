import unittest
import numpy as np
from event_mpc.coupled import INITIAL_STATE,NOMINAL_THETA,IntegrationSettings,advance
from event_mpc.prediction import rollout_event,predict


class PredictionTests(unittest.TestCase):
    def test_event_continuation_matches_continuous(self):
        a=rollout_event(INITIAL_STATE,NOMINAL_THETA)
        b=rollout_event(a.state,NOMINAL_THETA,a.time)
        self.assertEqual((a.status,b.status),('completed','completed'))
        continuous=advance(INITIAL_STATE,NOMINAL_THETA,stop='time',duration=b.time)
        np.testing.assert_allclose(b.state,continuous.state[:8,-1],atol=2e-6,rtol=1e-6)
        self.assertGreater(a.amplitude,0);self.assertLess(b.amplitude,0)
        self.assertGreater(a.work,0)

    def test_causal_horizon_and_all_states(self):
        r=predict(INITIAL_STATE,np.tile(NOMINAL_THETA,(4,1)))
        self.assertEqual(r.status,'completed')
        self.assertEqual(len(r.times),5)
        self.assertEqual(np.asarray(r.continuation).shape,(4,8))
        self.assertTrue(np.all(np.diff(r.times)>0))
        self.assertTrue(np.all(np.sign(r.amplitudes)==[1,-1,1,-1]))

    def test_failures_are_not_outputs(self):
        timeout=rollout_event(INITIAL_STATE,NOMINAL_THETA,settings=IntegrationSettings(timeout=.001))
        self.assertEqual(timeout.status,'timeout');self.assertIsNone(timeout.amplitude)
        small=INITIAL_STATE.copy();small[1]=.001
        missed=rollout_event(small,[0.,2.,1.5])
        self.assertEqual(missed.status,'missed_detector');self.assertIsNone(missed.work)
        still=INITIAL_STATE.copy();still[:2]=0
        self.assertEqual(rollout_event(still,NOMINAL_THETA).status,'grazing')
