import unittest
from dataclasses import replace
import numpy as np
from event_mpc.coupled import INITIAL_STATE,NOMINAL_THETA,IntegrationSettings,advance
from event_mpc.sensing import DetectorPairing


class CoupledTests(unittest.TestCase):
    def test_coupled_pulses_and_energy(self):
        r=advance(INITIAL_STATE,NOMINAL_THETA,stop='time',duration=.12)
        self.assertEqual(r.status,'completed')
        self.assertGreaterEqual(len(r.switches),4)
        from event_mpc.mechanics import MechanicalParameters,energy
        p=MechanicalParameters();e=energy(*r.state[:2],p)
        residual=e-e[0]-r.state[9]+r.state[11]
        self.assertLess(np.max(abs(residual))/e[0],1e-5)

    def test_sensor_reconstruction_and_causality(self):
        a=advance(INITIAL_STATE,NOMINAL_THETA)
        b=advance(a.state[:,-1],NOMINAL_THETA,start=a.time[-1],stop='detector')
        pairing=DetectorPairing();observations=[]
        for e in a.events+b.events:
            o=pairing.consume(e['detector'],e['time'])
            if o is not None:observations.append(o)
        self.assertEqual(len(observations),1)
        o=observations[0]
        self.assertLess(abs(o.crossing_time-a.time[-1]),2e-6)
        self.assertLess(abs(o.omega-a.state[1,-1])/abs(a.state[1,-1]),.002)
        self.assertGreater(o.available_time,a.time[-1])
        self.assertLess(o.omega,0)

    def test_pairing_failures(self):
        p=DetectorPairing()
        self.assertIsNone(p.consume('L',1.))
        self.assertIsNone(p.consume('L',1.001))
        self.assertIsNone(p.consume('R',1.010))
        self.assertIsNone(p.consume('R',1.009))
        self.assertEqual(p.rejected,['same_detector','pair_timeout','nonincreasing_timestamp'])

    def test_zero_and_refinement(self):
        a=advance(INITIAL_STATE,NOMINAL_THETA)
        b=advance(INITIAL_STATE,NOMINAL_THETA,settings=replace(IntegrationSettings(),rtol=1e-9,max_step=43.6575e-6))
        self.assertEqual(a.status,'completed')
        self.assertGreater(a.time[-1],.04)
        self.assertLess(abs(a.time[-1]-b.time[-1]),1e-7)
        np.testing.assert_allclose(a.state[:8,-1],b.state[:8,-1],atol=1e-5,rtol=1e-5)
