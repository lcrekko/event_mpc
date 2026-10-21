"""Six-state reciprocal HCO: manuscript (5), (26), (27), (29)."""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import expit

INITIAL_NEURONS = np.array([-.7739, -.4348, -.4461, -2.3198, -2.4326, -2.1535])


@dataclass(frozen=True)
class NeuronParameters:
    # Formula (27) rather than rounded Table II; fixed under gain changes.
    tau_fast: float = .05/286.320
    tau_slow: float = .5/286.320
    tau_ultraslow: float = 5./286.320
    synaptic_gain: float = -1.
    external_current: float = -1.
    threshold: float = 0.

    def __post_init__(self):
        if not all(np.isfinite(v) for v in vars(self).values()):
            raise ValueError('Finite neuron parameters required')
        if min(self.tau_fast,self.tau_slow,self.tau_ultraslow) <= 0 or self.synaptic_gain >= 0:
            raise ValueError('Positive time constants and inhibitory synapses required')


def neuron_rhs(t, state, gains=(2.,1.5), p=None):
    p = p or NeuronParameters()
    v = np.asarray(state).reshape(2,3)
    slow, ultra = gains
    result = np.empty((2,3))
    for i in range(2):
        syn = p.synaptic_gain*expit(2*(v[1-i,1]+1))
        result[i] = ((-v[i,0]+slow*np.tanh(v[i,1]+.9)-ultra*np.tanh(v[i,2]+.9)
                      +syn+p.external_current)/p.tau_fast,
                     (-v[i,1]+v[i,0])/p.tau_slow,
                     (-v[i,2]+v[i,0])/p.tau_ultraslow)
    return result.ravel()


def simulate_neurons(duration=.5, initial=None, gains=(2.,1.5), p=None,
                     rtol=1e-8, atol=1e-10, max_step=87.315e-6):
    p = p or NeuronParameters()
    initial = INITIAL_NEURONS.copy() if initial is None else np.asarray(initial,dtype=float)
    if initial.shape != (6,) or not np.all(np.isfinite(initial)) or duration <= 0:
        raise ValueError('Finite six-state initialization and positive duration required')
    events = []
    for index in (0,3):
        def event(t,y,index=index):
            return y[index]-p.threshold
        events.append(event)
    return solve_ivp(lambda t,y:neuron_rhs(t,y,gains,p),(0.,duration),initial,
                     rtol=rtol,atol=atol,max_step=max_step,events=events,dense_output=True)
