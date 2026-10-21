"""Independent/refined solver audit of frozen selected MPC sequences."""
import argparse
import json
from pathlib import Path
import numpy as np
from .coupled import IntegrationSettings
from .fast_prediction import parameter_arrays,sequence_prediction
from .mechanics import MechanicalParameters
from .neurons import NeuronParameters
from .prediction import predict


def audit(run):
    run=Path(run)
    actions=json.loads((run/'actions.json').read_text())
    index=json.loads((run/'search-index.json').read_text())
    meta=json.loads((run/'metadata.json').read_text())
    p=MechanicalParameters(**meta['predictor']);n=NeuronParameters(**meta['neurons'])
    pa,na=parameter_arrays(p,n);checks=[]
    with np.load(run/'search.npz') as data:
        events=json.loads((run/'events.json').read_text())['events']
        forecast_errors=[]
        for k,a in enumerate(actions[:len(events)]):
            entries=[d for d in index if d['event_index']==k]
            lo=entries[0]['offset'];hi=entries[-1]['offset']+entries[-1]['count']
            values=data['costs'][lo:hi];codes=data['statuses'][lo:hi]
            valid=np.isfinite(values)&(codes==0)
            if not np.any(valid):continue
            best=lo+int(np.argmin(np.where(valid,values,np.inf)))
            r=sequence_prediction(np.array(a['estimate']),data['sequences'][best],a['applied_time'],a['estimated_crossing'],pa,na)
            if r[-1]==0:
                forecast_errors.append({'event_index':k,
                    'first_crossing_error_s':float(r[0][1]-events[k]['true_time']),
                    'first_extremum_error_rad':float(r[1][0]-events[k]['amplitude'])})
        for k in (0,25,49):
            if k>=len(actions):
                checks.append({'event_index':k,'passed':False,'status':'unrun'});continue
            entries=[d for d in index if d['event_index']==k]
            lo=entries[0]['offset'];hi=entries[-1]['offset']+entries[-1]['count']
            costs=data['costs'][lo:hi];codes=data['statuses'][lo:hi]
            valid=np.isfinite(costs)&(codes==0)
            if not np.any(valid):
                checks.append({'event_index':k,'passed':False,'status':'no_valid_candidate'});continue
            best=lo+int(np.argmin(np.where(valid,costs,np.inf)))
            seq=data['sequences'][best];a=actions[k];x=np.array(a['estimate'])
            fast=sequence_prediction(x,seq,a['applied_time'],a['estimated_crossing'],pa,na)
            refined=sequence_prediction(x,seq,a['applied_time'],a['estimated_crossing'],pa,na,43.6575e-6,1e-9)
            reference=predict(x,seq,a['applied_time'],a['estimated_crossing'],p,n,IntegrationSettings())
            if fast[-1]!=0 or refined[-1]!=0 or reference.status!='completed':
                checks.append({'event_index':k,'passed':False,'status':'validity_mismatch'});continue
            errors={'reference_time_s':float(np.max(abs(fast[0]-reference.times))),
                    'reference_extremum_rad':float(np.max(abs(fast[1]-reference.amplitudes))),
                    'reference_work_J':float(np.max(abs(fast[2]-reference.work))),
                    'refinement_time_s':float(np.max(abs(fast[0]-refined[0]))),
                    'refinement_extremum_rad':float(np.max(abs(fast[1]-refined[1]))),
                    'refinement_work_J':float(np.max(abs(fast[2]-refined[2])))}
            limits={'reference_time_s':2e-7,'reference_extremum_rad':2e-6,'reference_work_J':2e-10,
                    'refinement_time_s':2e-7,'refinement_extremum_rad':2e-6,'refinement_work_J':2e-10}
            checks.append({'event_index':k,'status':'completed','passed':all(errors[key]<=bound for key,bound in limits.items()),
                           'errors':errors,'maximums':limits,'sequence':seq.tolist(),
                           'initial_estimate':x.tolist(),'application_time':a['applied_time']})
    from .__main__ import provenance
    return {'passed':all(c['passed'] for c in checks),'checks':checks,'one_step_forecast_errors':forecast_errors,
            'provenance':provenance(),
            'meaning':'Frozen selected sequences; no candidate reselection or closed-loop retuning'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=audit(a.run)
    with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
