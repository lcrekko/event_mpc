"""CPU JIT backend: adaptive RK4 step doubling with bracketed event restarts.

The independent SciPy hybrid solver is the reference. No fast-math or reduced
model is used. Numerical agreement must pass before this backend is used.
"""
import math
import numpy as np
from numba import njit,prange


@njit(cache=True)
def _rhs(y,theta,p,n,active):
    d=np.empty(9)
    a,w=y[0],y[1]
    tau=-p[3]*math.sin(a)*theta[0]**2 if active else 0.
    d[0]=w;d[1]=(tau-p[1]*w-p[2]*a)/p[0]
    for i in range(2):
        k=2+3*i;other=2+3*(1-i)
        z=2*(y[other+1]+1)
        sigmoid=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
        d[k]=(-y[k]+theta[1]*math.tanh(y[k+1]+.9)-theta[2]*math.tanh(y[k+2]+.9)+n[3]*sigmoid+n[4])/n[0]
        d[k+1]=(-y[k+1]+y[k])/n[1]
        d[k+2]=(-y[k+2]+y[k])/n[2]
    d[8]=abs(tau*w)
    return d


@njit(cache=True)
def _step(y,theta,p,n,active,h):
    k1=_rhs(y,theta,p,n,active)
    k2=_rhs(y+h*.5*k1,theta,p,n,active)
    k3=_rhs(y+h*.5*k2,theta,p,n,active)
    k4=_rhs(y+h*k3,theta,p,n,active)
    return y+h/6*(k1+2*k2+2*k3+k4)


@njit(cache=True)
def _fine(y,theta,p,n,active,h):
    return _step(_step(y,theta,p,n,active,h*.5),theta,p,n,active,h*.5)


@njit(cache=True)
def _root(y,theta,p,n,active,h,index,level):
    lo=0.;hi=h;left=y[index]-level
    for _ in range(40):
        mid=(lo+hi)*.5
        value=_fine(y,theta,p,n,active,mid)[index]-level
        if left*value<=0:hi=mid
        else:lo=mid;left=value
        if hi-lo<1e-12:break
    return (lo+hi)*.5


@njit(cache=True)
def interval(x,theta,p,n,hmax=87.315e-6,rtol=1e-7,timeout=.1,stop=0):
    """stop=0 next crossing, stop=1 outgoing sensor. Status codes below."""
    y=np.empty(9);y[:8]=x;y[8]=0.
    if abs(y[0])>=p[4]:return 0.,x.copy(),0.,0.,2
    if abs(y[0])<1e-12 and abs(y[1])<1e-8:return 0.,x.copy(),0.,0.,5
    direction=math.copysign(1.,y[0]) if abs(y[0])>1e-9 else math.copysign(1.,y[1])
    if stop==1:direction=1. if y[1]>0 else -1.
    active=y[2]>n[5]
    if abs(y[2]-n[5])<1e-8:active=_rhs(y,theta,p,n,active)[2]>0
    t=0.;h=hmax;amplitude=0.;turns=0
    atol=np.array([1e-10,1e-8,1e-9,1e-9,1e-9,1e-9,1e-9,1e-9,1e-15])
    gamma=.05*math.pi/180
    for _ in range(200000):
        if t>=timeout-1e-14:return t,y[:8].copy(),amplitude,y[8],1
        h=min(h,hmax,timeout-t)
        full=_step(y,theta,p,n,active,h);fine=_fine(y,theta,p,n,active,h)
        error=0.
        for k in range(9):
            scale=atol[k]+rtol*max(abs(y[k]),abs(fine[k]))
            error=max(error,abs(fine[k]-full[k])/(15*scale))
        if not math.isfinite(error):return t,y[:8].copy(),amplitude,y[8],6
        factor=2. if error==0 else min(2.,max(.2,.9*error**(-.2)))
        if error>1:
            h*=factor
            if h<1e-13:return t,y[:8].copy(),amplitude,y[8],6
            continue
        hit=h+1.;kind=-1
        if (active and fine[2]<n[5]) or (not active and fine[2]>n[5]):
            root=_root(y,theta,p,n,active,h,2,n[5])
            if root<hit:hit=root;kind=0
        if stop==0:
            crossed=direction*fine[0]<=0 and direction*y[0]>0
            level=0.
        else:
            crossed=direction*fine[0]>=gamma and direction*y[0]<gamma
            level=direction*gamma
        if crossed:
            root=_root(y,theta,p,n,active,h,0,level)
            if root<hit:hit=root;kind=1
        if y[1]*fine[1]<0:
            root=_root(y,theta,p,n,active,h,1,0.)
            if root<hit:hit=root;kind=2
        if abs(fine[0])>=p[4]:
            root=_root(y,theta,p,n,active,h,0,math.copysign(p[4],fine[0]))
            if root<hit:hit=root;kind=3
        if kind>=0:
            y=_fine(y,theta,p,n,active,hit);t+=hit
            if kind==0:active=not active
            elif kind==1:
                if stop==0:
                    if abs(y[1])<1e-8:return t,y[:8].copy(),amplitude,y[8],5
                    if abs(amplitude)<gamma:return t,y[:8].copy(),amplitude,y[8],3
                    if turns!=1:return t,y[:8].copy(),amplitude,y[8],4
                return t,y[:8].copy(),amplitude,y[8],0
            elif kind==2:
                # Starting infinitesimally before a located root must not count it twice.
                if abs(y[0])>abs(amplitude)+1e-10:
                    amplitude=y[0];turns+=1
            else:return t,y[:8].copy(),amplitude,y[8],2
            h=min(hmax,h*factor)
        else:
            y=fine;t+=h;h*=factor
    return t,y[:8].copy(),amplitude,y[8],6


@njit(cache=True)
def sequence_prediction(x,sequence,start,crossing,p,n,hmax=87.315e-6,rtol=1e-7,timeout=.1):
    N=len(sequence);times=np.empty(N+1);amplitudes=np.empty(N);works=np.empty(N)
    states=np.empty((N,8));times[:]=np.nan;amplitudes[:]=np.nan;works[:]=np.nan;states[:]=np.nan
    times[0]=crossing;t=start;state=x.copy();prefix=0.
    for j in range(N):
        dt,state,a,q,status=interval(state,sequence[j],p,n,hmax,rtol,timeout,0)
        if status!=0:return times,amplitudes,works,states,status
        t+=dt;times[j+1]=t;amplitudes[j]=a;works[j]=prefix+q;states[j]=state
        if j+1<N:
            dt,state,a,q,status=interval(state,sequence[j],p,n,hmax,rtol,timeout,1)
            if status!=0:return times,amplitudes,works,states,status
            t+=dt;prefix=q
    return times,amplitudes,works,states,0


@njit(cache=True,parallel=True)
def batch_cost(x,sequences,start,crossing,event_index,p,n,weights,hmax,rtol,timeout):
    costs=np.full(len(sequences),np.inf);statuses=np.empty(len(sequences),dtype=np.int64)
    for i in prange(len(sequences)):
        times,amps,works,states,status=sequence_prediction(x,sequences[i],start,crossing,p,n,hmax,rtol,timeout)
        statuses[i]=status
        if status==0:
            total=0.
            for j in range(len(amps)):
                ref_time=(event_index+j)*weights[0]
                ref_amp=weights[1] if (event_index+j)%2==0 else -weights[1]
                total+=weights[4]**j*((ref_time-times[j])**2+weights[2]*(ref_amp-amps[j])**2+weights[3]*works[j])
            costs[i]=total
    return costs,statuses


def parameter_arrays(p,n):
    return (np.array([p.inertia,p.damping,p.stiffness,p.kappa,p.angle_limit,p.current_limit]),
            np.array([n.tau_fast,n.tau_slow,n.tau_ultraslow,n.synaptic_gain,n.external_current,n.threshold]))


STATUS_NAMES={0:'completed',1:'timeout',2:'angle_limit',3:'missed_detector',
              4:'invalid_turning_points',5:'grazing',6:'integration_failed'}
