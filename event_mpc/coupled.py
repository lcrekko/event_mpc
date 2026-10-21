"""Reference hybrid integration, equations (1), (2), (5), (6), (16), (19).

Full state is simulator-only. Sensor observations are constructed separately.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.integrate import solve_ivp
from .mechanics import MechanicalParameters, torque
from .neurons import NeuronParameters, INITIAL_NEURONS, neuron_rhs

INITIAL_STATE=np.r_[0.,5.5137,INITIAL_NEURONS]
NOMINAL_THETA=np.array([.032606,2.,1.5])
GAMMA_S=np.deg2rad(.05)


@dataclass(frozen=True)
class IntegrationSettings:
    rtol: float=1e-7
    atol: tuple=(1e-10,1e-8,1e-9,1e-9,1e-9,1e-9,1e-9,1e-9,1e-15,1e-15,1e-15,1e-15)
    max_step: float=87.315e-6
    timeout: float=.1


@dataclass
class Segment:
    time: np.ndarray
    state: np.ndarray
    status: str
    events: list=field(default_factory=list)
    turning: list=field(default_factory=list)
    switches: list=field(default_factory=list)
    nfev: int=0


def joint_rhs(t,y,theta,p,n,active):
    a,w=y[:2]; current=theta[0] if active else 0.
    tau=torque(a,current,p)
    return np.r_[w,(tau-p.damping*w-p.stiffness*a)/p.inertia,
                 neuron_rhs(t,y[2:8],theta[1:],n),abs(tau*w),tau*w,
                 -p.kappa*current**2*a*w,p.damping*w*w]


def advance(state,theta,start=0.,p=None,n=None,settings=None,stop='zero',duration=None):
    """Advance to next zero, outgoing detector, or finite duration.

    Pulse onset/termination is located as a terminal root and the integrator
    restarts with the opposite active branch. No state resets are performed.
    """
    p=p or MechanicalParameters();n=n or NeuronParameters();s=settings or IntegrationSettings()
    x=np.asarray(state,dtype=float)
    if x.shape==(8,):x=np.r_[x,np.zeros(4)]
    theta=np.asarray(theta,dtype=float)
    if (x.shape!=(12,) or not np.all(np.isfinite(x)) or theta.shape!=(3,)
            or not np.all(np.isfinite(theta)) or not 0<=theta[0]<=p.current_limit):
        raise ValueError('Finite state and admissible current required')
    if abs(x[0])>=p.angle_limit:
        return Segment(np.array([start]),x[:,None],'angle_limit')
    if stop not in ('zero','detector','time'):raise ValueError('Unknown integration stop')
    if stop=='zero' and abs(x[0])<1e-12 and abs(x[1])<1e-8:
        return Segment(np.array([start]),x[:,None],'grazing')
    sign=np.sign(x[0]) if abs(x[0])>1e-12 else np.sign(x[1])
    if stop=='detector': sign=np.sign(x[1])
    end=start+(duration if duration is not None else s.timeout)
    if not np.isfinite(end) or end<=start:raise ValueError('Positive finite duration required')
    active=x[2]>n.threshold or (abs(x[2]-n.threshold)<1e-10 and neuron_rhs(start,x[2:8],theta[1:],n)[0]>0)
    times=[];states=[];events=[];turns=[];switches=[];nfev=0
    t=start;status='timeout' if stop!='time' else 'completed'
    for _ in range(10000):
        def pulse(t,y):return y[2]-n.threshold
        pulse.terminal=True;pulse.direction=-1 if active else 1
        def target(t,y):return y[0] if stop=='zero' else y[0]-sign*GAMMA_S
        target.terminal=stop!='time';target.direction=-sign if stop=='zero' else sign
        def limit(t,y):return p.angle_limit-abs(y[0])
        limit.terminal=True;limit.direction=-1
        def left(t,y):return y[0]-GAMMA_S
        def right(t,y):return y[0]+GAMMA_S
        def turning(t,y):return y[1]
        sol=solve_ivp(lambda t,y:joint_rhs(t,y,theta,p,n,active),(t,end),x,
                      rtol=s.rtol,atol=s.atol,max_step=s.max_step,
                      events=(pulse,target,limit,left,right,turning))
        nfev+=sol.nfev
        if times:
            times[-1]=times[-1][:-1];states[-1]=states[-1][:,:-1]
        times.append(sol.t);states.append(sol.y)
        for idx,label in ((3,'L'),(4,'R')):
            for et,ey in zip(sol.t_events[idx],sol.y_events[idx]):
                if et>start+1e-12:events.append({'time':float(et),'detector':label})
        for et,ey in zip(sol.t_events[5],sol.y_events[5]):
            if et>start+1e-12 and abs(joint_rhs(et,ey,theta,p,n,active)[1])>1e-8:
                if not turns or et-turns[-1]['time']>1e-10:
                    turns.append({'time':float(et),'angle':float(ey[0])})
        if not sol.success:status='integration_failed';break
        if len(sol.t_events[2]):status='angle_limit';break
        if stop!='time' and len(sol.t_events[1]):
            if stop=='detector':
                label='L' if sign>0 else 'R'
                et=float(sol.t[-1])
                if not any(e['detector']==label and abs(e['time']-et)<1e-10 for e in events):
                    events.append({'time':et,'detector':label})
            status='completed';break
        if len(sol.t_events[0]):
            if sol.t[-1]<=t+1e-14:status='switch_stall';break
            t=float(sol.t[-1]);x=sol.y[:,-1];active=not active
            switches.append({'time':t,'active':bool(active)})
            if t>=end-1e-14:break
        else:break
    else:status='switch_limit'
    return Segment(np.concatenate(times),np.concatenate(states,axis=1),status,
                   sorted(events,key=lambda e:e['time']),turns,switches,nfev)
