"""Reproduce bounded B/C/D evidence without running controller experiments."""
import argparse
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
import numpy as np
from .__main__ import write_json,provenance
from .neurons import NeuronParameters,INITIAL_NEURONS,simulate_neurons,neuron_rhs
from .coupled import INITIAL_STATE,NOMINAL_THETA,IntegrationSettings,advance
from .mechanics import MechanicalParameters
from .sensing import DetectorPairing
from .prediction import predict


def generate(milestone,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    if milestone=='b':
        a=simulate_neurons(.5);b=simulate_neurons(.5,rtol=1e-10,atol=1e-12,max_step=43.6575e-6)
        if not a.success or not b.success:raise RuntimeError('Neuron integration failed')
        upward=a.t_events[0][[neuron_rhs(t,a.sol(t))[0]>0 for t in a.t_events[0]]]
        np.savez_compressed(output/'neurons.npz',time=a.t,state=a.y,events_A=a.t_events[0],events_B=a.t_events[1])
        result={'success':a.success,'upcrossings_A':upward.tolist(),'last_periods_s':np.diff(upward)[-5:].tolist(),
                'max_event_refinement_error_s':float(max(abs(a.t_events[0]-b.t_events[0]))),
                'parameters':asdict(NeuronParameters()),'initial':INITIAL_NEURONS.tolist(),'gains':[2,1.5],
                'solver':{'method':'RK45','rtol':1e-8,'atol':1e-10,'max_step':87.315e-6},'provenance':provenance()}
        write_json(output/'validation.json',result)
    elif milestone=='c':
        pair=DetectorPairing();x=INITIAL_STATE.copy();t=0.;ts=[];ys=[];observations=[];detectors=[];switches=[]
        for k in range(10):
            a=advance(x,NOMINAL_THETA,t)
            if a.status!='completed':raise RuntimeError(a.status)
            b=advance(a.state[:,-1],NOMINAL_THETA,a.time[-1],stop='detector')
            if b.status!='completed':raise RuntimeError(b.status)
            for segment in (a,b):
                ts.extend(segment.time.tolist());ys.extend(segment.state.T.tolist());switches.extend(segment.switches)
                for e in segment.events:
                    detectors.append(e);o=pair.consume(e['detector'],e['time'])
                    if o is not None:observations.append({**asdict(o),'true_time':float(a.time[-1]),'true_omega':float(a.state[1,-1])})
            x=b.state[:8,-1];t=float(b.time[-1])
        np.savez_compressed(output/'coupled.npz',time=ts,state=np.asarray(ys).T)
        result={'observations':observations,'detector_events':detectors,'switches':switches,
                'pair_rejections':pair.rejected,'configuration':{'theta':NOMINAL_THETA.tolist(),
                'initial':INITIAL_STATE.tolist(),'integration':asdict(IntegrationSettings()),
                'neurons':asdict(NeuronParameters()),'mechanics':asdict(MechanicalParameters())},'provenance':provenance()}
        write_json(output/'sensing.json',result)
    elif milestone=='d':
        start=perf_counter();r=predict(INITIAL_STATE,np.tile(NOMINAL_THETA,(4,1)))
        result={'prediction':asdict(r),'wall_seconds':perf_counter()-start,
                'configuration':{'initial':INITIAL_STATE.tolist(),'sequence':np.tile(NOMINAL_THETA,(4,1)).tolist(),
                                 'settings':asdict(IntegrationSettings())},'provenance':provenance()}
        write_json(output/'prediction.json',result)
        if r.status!='completed':raise RuntimeError(r.status)
    else:raise ValueError('Choose milestone b, c or d')
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('milestone',choices=['b','c','d'])
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(generate(a.milestone,a.output))
