import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from event_mpc.closed_loop import run_closed_loop,estimate_at_availability
from event_mpc.optimization import SearchSettings,shifted


class ClosedLoopTests(unittest.TestCase):
    def test_causal_updates_best_candidate_and_warm_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'run'
            result=run_closed_loop(p,2,1,SearchSettings(samples=4))
            self.assertEqual(result['status'],'completed')
            actions=json.loads((p/'actions.json').read_text())
            events=json.loads((p/'events.json').read_text())['events']
            self.assertEqual(actions[1]['applied_time'],events[0]['observation']['available_time'])
            self.assertGreater(actions[1]['applied_time'],events[0]['true_time'])
            self.assertGreater(actions[1]['applied_time'],actions[1]['estimated_crossing'])
            index=json.loads((p/'search-index.json').read_text())
            count=sum(d['count'] for d in index if d['event_index']==0)
            with np.load(p/'search.npz') as data:
                costs=data['costs'][:count];best=data['sequences'][np.argmin(costs)]
                np.testing.assert_array_equal(actions[0]['theta'],best[0])
                np.testing.assert_array_equal(data['sequences'][count],shifted(best))
            self.assertEqual(result['completed_intervals'],2)

    def test_no_truth_state_in_controller_interface(self):
        import inspect
        signature=inspect.signature(estimate_at_availability)
        self.assertEqual(list(signature.parameters),['observation','known_neurons','known_time',
                                                      'old_theta','p','n','settings'])
