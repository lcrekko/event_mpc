"""Event-to-event continuation and causal candidate sequences, (10), (16)–(19)."""
from dataclasses import dataclass,field
import numpy as np
from .coupled import advance,GAMMA_S


@dataclass
class EventRollout:
    status: str
    time: float
    state: np.ndarray
    amplitude: float | None
    work: float | None
    segment: object=None


def rollout_event(state,theta,start=0.,p=None,n=None,settings=None):
    r=advance(state,theta,start,p,n,settings)
    status=r.status
    amplitude=None;work=None
    if status=='completed':
        if abs(r.state[1,-1])<1e-8:status='grazing'
        elif len(r.turning)!=1:status='invalid_turning_points'
        elif abs(r.turning[0]['angle'])<GAMMA_S:status='missed_detector'
        else:
            amplitude=float(r.turning[0]['angle']);work=float(r.state[8,-1])
    return EventRollout(status,float(r.time[-1]),r.state[:8,-1].copy(),amplitude,work,r)


@dataclass
class Prediction:
    status: str
    times: list=field(default_factory=list)
    amplitudes: list=field(default_factory=list)
    work: list=field(default_factory=list)
    continuation: list=field(default_factory=list)


def predict(state,sequence,start=0.,crossing_time=None,p=None,n=None,settings=None):
    """N future crossings with causal changes at outgoing detector availability.

    Initial state is an estimate supplied by controller, not simulator truth.
    After every predicted crossing except the last, old parameters remain until
    the outgoing detector; that work belongs to the following event interval.
    """
    x=np.asarray(state).copy();t=start
    result=Prediction('completed',[start if crossing_time is None else crossing_time])
    prefix=0.
    for j,theta in enumerate(sequence):
        r=rollout_event(x,theta,t,p,n,settings)
        if r.status!='completed':result.status=r.status;return result
        result.times.append(r.time);result.amplitudes.append(r.amplitude)
        result.work.append(prefix+r.work);result.continuation.append(r.state.tolist())
        x=r.state;t=r.time
        if j+1<len(sequence):
            delay=advance(x,theta,t,p,n,settings,stop='detector')
            if delay.status!='completed':result.status='detector_'+delay.status;return result
            x=delay.state[:8,-1];t=float(delay.time[-1]);prefix=float(delay.state[8,-1])
    return result
