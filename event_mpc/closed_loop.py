"""Causal sensor-only closed loop; plant and predictor remain distinct objects."""
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.integrate import solve_ivp
from .coupled import INITIAL_STATE,NOMINAL_THETA,IntegrationSettings,advance
from .neurons import NeuronParameters,neuron_rhs
from .mechanics import MechanicalParameters
from .sensing import DetectorPairing,Observation
from .optimization import SearchSettings,optimize,shifted
from .objective import Objective
from .fast_prediction import batch_cost,parameter_arrays,STATUS_NAMES


def estimate_at_availability(observation,known_neurons,known_time,old_theta,p,n,settings):
    """Only detector observation and known internal circuit state are accepted.

    Reconstruct at the estimated timestamp, then propagate to availability with
    the previously applied parameters. Never read plant alpha/omega here.
    """
    if observation.crossing_time<known_time or observation.available_time<observation.crossing_time:
        raise ValueError('Noncausal observation')
    sol=solve_ivp(lambda t,y:neuron_rhs(t,y,old_theta[1:],n),
                  (known_time,observation.crossing_time),known_neurons,
                  rtol=settings.rtol,atol=1e-9,max_step=settings.max_step)
    if not sol.success:raise RuntimeError('Circuit history integration failed')
    x=np.r_[0.,observation.omega,sol.y[:,-1]]
    delay=observation.available_time-observation.crossing_time
    if delay==0:return x,0.
    r=advance(x,old_theta,observation.crossing_time,p,n,settings,stop='time',duration=delay)
    if r.status!='completed':raise RuntimeError('State propagation to availability failed: '+r.status)
    return r.state[:8,-1].copy(),float(r.state[8,-1])


def run_closed_loop(output,intervals=50,seed=1,search=None,plant_parameters=None,
                    predictor_parameters=None,integration=None,initial=None,description='nominal',
                    initial_theta=None,startup_intervals=0):
    from .__main__ import write_json,provenance
    from importlib.metadata import version
    if intervals<1:raise ValueError('Positive interval count required')
    if not isinstance(startup_intervals,int) or not 0<=startup_intervals<=intervals:
        raise ValueError('Startup intervals must be an integer between zero and intervals')
    s=search or SearchSettings();settings=integration or IntegrationSettings()
    plant=plant_parameters or MechanicalParameters();predictor=predictor_parameters or MechanicalParameters()
    neurons=NeuronParameters();objective=Objective();pa,na=parameter_arrays(predictor,neurons)
    x=INITIAL_STATE.copy() if initial is None else np.asarray(initial,dtype=float).copy()
    if x.shape!=(8,) or not np.all(np.isfinite(x)):raise ValueError('Finite eight-state initial condition required')
    old_theta=NOMINAL_THETA.copy() if initial_theta is None else np.asarray(initial_theta,dtype=float).copy()
    if (old_theta.shape!=(3,) or not np.all(np.isfinite(old_theta)) or
            not 0<=old_theta[0]<=min(plant.current_limit,predictor.current_limit) or np.any(old_theta[1:]<=0)):
        raise ValueError('Finite initial theta, admissible current and positive gains required')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    plant_state=np.r_[x,np.zeros(4)];estimate=x.copy();known_neurons=x[2:].copy();known_time=0.
    time=0.;crossing=0.;mean=None;rng=np.random.default_rng(seed);prefix_work=0.
    pair=DetectorPairing();ts=[];ys=[];actions=[];events=[];detections=[];switches=[]
    candidates=[];costs=[];statuses=[];diagnostic_index=[];offset=0;last_cross_work=0.
    metadata={'description':description,'intervals':intervals,'seed':seed,'search':asdict(s),
              'plant':asdict(plant),'predictor':asdict(predictor),'neurons':asdict(neurons),
              'integration':asdict(settings),'initial_state':x.tolist(),
              'initial_theta':old_theta.tolist(),'startup_intervals':startup_intervals,
              'objective':asdict(objective),'objective_weights':objective.array().tolist(),
              'information':'detector timestamps plus owned circuit state; no measured plant state',
              'delay':'sensing delay causal; optimizer wall time measured but not injected into simulated time',
              'provenance':provenance(seed,'NumPy default_rng PCG64; candidate draws generated before parallel evaluation'),
              'numba':version('numba'),'llvmlite':version('llvmlite')}
    write_json(output/'metadata.json',metadata)
    warm_start=perf_counter()
    batch_cost(estimate,np.tile(old_theta,(1,s.horizon,1)),0.,0.,0,pa,na,objective.array(),settings.max_step,settings.rtol,settings.timeout)
    warm_seconds=perf_counter()-warm_start
    status='completed';start_wall=perf_counter()
    for k in range(intervals):
        def evaluate(sequences):
            values,codes=batch_cost(estimate,sequences,time,crossing,k,pa,na,objective.array(),
                                    settings.max_step,settings.rtol,settings.timeout)
            return values+objective.array()[3]*prefix_work,codes
        startup=k<startup_intervals
        active_search=SearchSettings(horizon=s.horizon,method='fixed',lower=s.lower,upper=s.upper) if startup else s
        before=perf_counter();selection=optimize(evaluate,rng,active_search,
                                                 None if startup else mean,old_theta)
        optimization_seconds=perf_counter()-before
        theta=selection.sequence[0].copy()
        actions.append({'event_index':k,'estimated_crossing':crossing,'applied_time':time,
                        'theta':theta.tolist(),'estimate':estimate.tolist(),'fallback':selection.fallback,
                        'startup':startup,
                        'cost':None if not np.isfinite(selection.cost) else selection.cost,
                        'optimization_seconds':optimization_seconds})
        for d in selection.diagnostics:
            candidates.append(d['sequences']);costs.append(d['costs']);statuses.append(d['statuses'])
            diagnostic_index.append({'event_index':k,'label':d['label'],'offset':offset,'count':len(d['costs'])})
            offset+=len(d['costs'])
        a=advance(plant_state,theta,time,plant,neurons,settings)
        for segment in [a]:
            ts.extend(segment.time.tolist());ys.extend(segment.state.T.tolist());switches.extend(segment.switches)
        if a.status!='completed':status='plant_'+a.status;break
        if len(a.turning)!=1:status='plant_invalid_turning_points';break
        event={'event_index':k+1,'true_time':float(a.time[-1]),'true_omega':float(a.state[1,-1]),
               'amplitude':a.turning[0]['angle'],'absolute_work':float(a.state[8,-1]-last_cross_work)}
        last_cross_work=float(a.state[8,-1])
        b=advance(a.state[:,-1],theta,float(a.time[-1]),plant,neurons,settings,stop='detector')
        ts.extend(b.time.tolist());ys.extend(b.state.T.tolist());switches.extend(b.switches)
        if b.status!='completed':status='plant_detector_'+b.status;break
        observation=None
        for e in a.events+b.events:
            detections.append(e);o=pair.consume(e['detector'],e['time'])
            if o is not None:observation=o
        if observation is None:status='missing_detector_pair';break
        event['observation']=asdict(observation);events.append(event)
        # Known internal neurons are propagated from the last application; truth
        # alpha/omega and actual crossing timestamp do not enter this function.
        estimate,prefix_work=estimate_at_availability(observation,known_neurons,known_time,theta,
                                                      predictor,neurons,settings)
        known_neurons=estimate[2:].copy();known_time=observation.available_time
        plant_state=b.state[:,-1];time=observation.available_time;crossing=observation.crossing_time
        old_theta=theta;mean=shifted(selection.sequence)
        if (k+1)%10==0:print(f'{output.name}: {k+1}/{intervals} intervals',flush=True)
    elapsed=perf_counter()-start_wall
    np.savez_compressed(output/'trajectory.npz',time=np.asarray(ts),state=np.asarray(ys).T)
    if candidates:
        np.savez_compressed(output/'search.npz',sequences=np.concatenate(candidates),
                            costs=np.concatenate(costs),statuses=np.concatenate(statuses))
    write_json(output/'events.json',{'events':events,'detections':detections,'switches':switches,
                                     'rejected_pairs':pair.rejected})
    write_json(output/'actions.json',actions);write_json(output/'search-index.json',diagnostic_index)
    outcome={'status':status,'completed_intervals':len(events),'requested_intervals':intervals,
             'warmup_seconds':warm_seconds,'wall_seconds':elapsed,'status_codes':STATUS_NAMES}
    write_json(output/'status.json',outcome)
    return outcome


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--intervals',type=int,default=50)
    parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--samples',type=int,default=256)
    parser.add_argument('--method',choices=['refinement','uniform','fixed'],default='refinement')
    parser.add_argument('--constant',action='store_true')
    args=parser.parse_args()
    r=run_closed_loop(args.output,args.intervals,args.seed,
                      SearchSettings(samples=args.samples,method=args.method,constant_parameters=args.constant))
    print(json.dumps(r,indent=2));return 0 if r['status']=='completed' else 1


if __name__=='__main__':raise SystemExit(main())
