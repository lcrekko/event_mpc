from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from event_mpc.mechanics import MechanicalParameters,torque
from event_mpc.paper_figures import actuation_series,performance_series


class PaperDataTests(unittest.TestCase):
    def test_right_continuous_actions_and_switches_define_exact_torque(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);model=MechanicalParameters()
            def write(name,obj):(p/name).write_text(json.dumps(obj))
            write('metadata.json',{'plant':asdict(model),'initial_state':[0,0,-1,0,0,0,0,0],
                                   'neurons':{'threshold':0}})
            write('actions.json',[{'applied_time':0.,'theta':[.05,1.5,2.]},
                                   {'applied_time':.2,'theta':[.1,2.,1.5]}])
            write('events.json',{'events':[{'true_time':.3}],
                                 'switches':[{'time':.1,'active':True},{'time':.3,'active':False}]})
            state=np.zeros((12,5));state[0]=.01;state[2]=[-1,0,0,1,0]
            np.savez(p/'trajectory.npz',time=[0.,.1,.1,.2,.3],state=state)
            series=actuation_series(p)
            np.testing.assert_array_equal(series['current'],[0.,.05,.05,.1,0.])
            np.testing.assert_allclose(series['torque'],torque(.01,np.array([0.,.05,.05,.1,0.]),model))

    def test_figure_quantities_preserve_units_and_timing_sign(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'metadata.json').write_text(json.dumps({'objective':{'period':.05}}))
            (p/'events.json').write_text(json.dumps({'events':[
                {'true_time':.049,'event_index':1,'amplitude':np.deg2rad(4.),'absolute_work':1e-7},
                {'true_time':.102,'event_index':2,'amplitude':-np.deg2rad(5.),'absolute_work':2e-7}]}))
            s=performance_series(p)
            np.testing.assert_allclose(s['amplitude'],[4.,5.])
            np.testing.assert_allclose(s['timing_error'],[-1.,2.])
            np.testing.assert_allclose(s['work'],[.1,.2])
