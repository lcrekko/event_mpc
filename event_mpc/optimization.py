"""Projected Gaussian refinement (20)–(23), plus manuscript alternatives."""
from dataclasses import dataclass,field
import numpy as np
from .coupled import NOMINAL_THETA

LOWER=np.array([0.,1.8,1.3]);UPPER=np.array([.12,2.2,1.7])


@dataclass(frozen=True)
class SearchSettings:
    horizon: int=4
    samples: int=256
    rounds: int=2
    temperature: float=250e-6  # 250 ms² in s²
    sigma: tuple=(.012,.04,.04)
    method: str='refinement'
    constant_parameters: bool=False
    lower: tuple=(0.,1.8,1.3)
    upper: tuple=(.12,2.2,1.7)

    def __post_init__(self):
        if self.horizon<1 or self.samples<2 or self.rounds<1 or self.temperature<=0:
            raise ValueError('Positive horizon/rounds/temperature, >=2 samples required')
        if self.method not in ('refinement','uniform','fixed'):raise ValueError('Unknown search')
        if len(self.sigma)!=3 or min(self.sigma)<0:raise ValueError('Three nonnegative sampling deviations required')
        lo=np.asarray(self.lower);hi=np.asarray(self.upper)
        if (lo.shape!=(3,) or hi.shape!=(3,) or not np.all(np.isfinite(lo))
                or not np.all(np.isfinite(hi)) or np.any(lo>=hi)
                or lo[0]<0 or np.any(lo[1:]<=0)):
            raise ValueError('Finite ordered bounds for current and positive gains required')


@dataclass
class SearchResult:
    sequence: np.ndarray
    cost: float
    fallback: bool
    diagnostics: list=field(default_factory=list)


def shifted(sequence):
    return np.concatenate([sequence[1:],sequence[-1:]],axis=0)


def optimize(evaluate,rng,settings=None,nominal=None,previous_theta=None):
    """Evaluate returns (costs, status_codes) for an array [M,N,3].

    Initial mean is repeated nominal theta. Each of R rounds includes its
    mean plus M-1 projected draws. Also evaluate each newly updated mean,
    including the final one. Keep best valid candidate across all rounds.
    If one round has no valid candidate retain its mean and sample next round;
    if no evaluation is valid use the documented zero-current/retained-gain action.
    """
    s=settings or SearchSettings()
    lower=np.asarray(s.lower);upper=np.asarray(s.upper)
    prior=NOMINAL_THETA if previous_theta is None else np.asarray(previous_theta)
    mean=np.tile(prior,(s.horizon,1)) if nominal is None else np.asarray(nominal).copy()
    if mean.shape!=(s.horizon,3) or not np.all(np.isfinite(mean)):
        raise ValueError('Finite N by 3 nominal sequence required')
    # Uniform shooting does not sample around its nominal/previous parameters;
    # a user-specified startup or fixed baseline may be outside the search box.
    if s.method=='refinement' and (np.any(mean<lower) or np.any(mean>upper)):
        raise ValueError('Nominal sequence outside bounds')
    if s.constant_parameters:mean=np.tile(mean[0],(s.horizon,1))
    best=None;best_cost=float('inf');history=[]

    def assess(candidates,label):
        nonlocal best,best_cost
        costs,statuses=evaluate(candidates)
        valid=np.isfinite(costs)&(np.asarray(statuses)==0)
        history.append({'label':label,'sequences':candidates.copy(),
                        'costs':costs.copy(),'statuses':np.asarray(statuses).copy()})
        if np.any(valid):
            eligible=np.where(valid,costs,np.inf);k=int(np.argmin(eligible))
            if costs[k]<best_cost:best=candidates[k].copy();best_cost=float(costs[k])
        return costs,valid

    if s.method=='fixed':assess(mean[None],'fixed')
    elif s.method=='uniform':
        shape=(s.samples,1 if s.constant_parameters else s.horizon,3)
        candidates=rng.uniform(lower,upper,size=shape)
        if s.constant_parameters:candidates=np.repeat(candidates,s.horizon,axis=1)
        assess(candidates,'uniform')
    else:
        for r in range(s.rounds):
            shape=(s.samples-1,1 if s.constant_parameters else s.horizon,3)
            noise=rng.normal(size=shape)*np.array(s.sigma)
            if s.constant_parameters:noise=np.repeat(noise,s.horizon,axis=1)
            candidates=np.concatenate([mean[None],np.clip(mean+noise,lower,upper)],axis=0)
            costs,valid=assess(candidates,f'round_{r}')
            if np.any(valid):
                rho=np.min(costs[valid]);weights=np.exp(-(costs[valid]-rho)/s.temperature)
                weights/=weights.sum();mean=np.sum(weights[:,None,None]*candidates[valid],axis=0)
                assess(mean[None],f'updated_mean_{r}')
    if best is None:
        fallback=prior.copy();fallback[0]=0.
        return SearchResult(np.tile(fallback,(s.horizon,1)),float('inf'),True,history)
    return SearchResult(best,best_cost,False,history)
