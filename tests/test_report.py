from pathlib import Path
import json
import tempfile
import unittest
import numpy as np
from event_mpc.report import summarize_run
from event_mpc.mechanics import MechanicalParameters
from dataclasses import asdict


class ReportTests(unittest.TestCase):
    def fixture(self,path,status):
        # Synthetic saved-data fixture; this does not purport to be a physical trajectory.
        def write(name,obj):(path/name).write_text(json.dumps(obj))
        write('metadata.json',{'objective':{'period':.05,'amplitude':np.deg2rad(5)},
             'plant':asdict(MechanicalParameters()),'intervals':50,'seed':1,'search':{'method':'refinement'}})
        write('status.json',{'status':status,'wall_seconds':1.})
        write('events.json',{'events':[{'event_index':1,'true_time':.05,'true_omega':-5.,
              'amplitude':np.deg2rad(5),'absolute_work':1e-7,
              'observation':{'crossing_time':.05,'available_time':.0502,'omega':-5.}}]})
        write('actions.json',[{'optimization_seconds':.1,'fallback':True}])
        np.savez(path/'search.npz',statuses=[0,1])
        state=np.zeros((12,2));state[1,:]=5.
        np.savez(path/'trajectory.npz',time=[0.,.05],state=state)

    def test_metric_units_and_invalid_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.fixture(p,'completed');r=summarize_run(p)
            self.assertEqual(r['timing_rms_ms'],0.)
            self.assertEqual(r['amplitude_rms_deg'],0.)
            self.assertAlmostEqual(r['absolute_work_uJ'],.1)
            self.assertEqual(r['invalid_candidate_fraction'],.5)
            self.assertAlmostEqual(r['optimization_to_interval_p95'],2.)
            self.assertEqual(r['fallback_count'],1)

    def test_truncated_status_is_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.fixture(p,'plant_timeout');r=summarize_run(p)
            self.assertEqual(r['status'],'plant_timeout')
            self.assertEqual((r['completed_intervals'],r['requested_intervals']),(1,50))
