"""Reproducible predictor accuracy/performance comparison after JIT warmup."""
from pathlib import Path
from time import perf_counter
import numpy as np
from .coupled import INITIAL_STATE,NOMINAL_THETA
from .mechanics import MechanicalParameters
from .neurons import NeuronParameters
from .objective import Objective
from .prediction import predict
from .fast_prediction import batch_cost,parameter_arrays


def profile():
    from .__main__ import provenance
    p=MechanicalParameters();n=NeuronParameters();obj=Objective();pa,na=parameter_arrays(p,n)
    rng=np.random.default_rng(17)
    seq=np.clip(np.tile(NOMINAL_THETA,(256,4,1))+rng.normal(size=(256,4,3))*[.012,.04,.04],
                [0.,1.8,1.3],[.12,2.2,1.7])
    before=perf_counter();batch_cost(INITIAL_STATE,seq[:1],0.,0.,0,pa,na,obj.array(),87.315e-6,1e-7,.1)
    warmup=perf_counter()-before
    before=perf_counter();values,statuses=batch_cost(INITIAL_STATE,seq,0.,0.,0,pa,na,obj.array(),87.315e-6,1e-7,.1)
    fast_seconds=perf_counter()-before
    errors=[];before=perf_counter()
    for i in range(5):
        r=predict(INITIAL_STATE,seq[i])
        if r.status!='completed' or statuses[i]!=0:raise RuntimeError('Profile validity mismatch')
        errors.append(abs(obj.evaluate(r,0)-values[i]))
    reference_seconds=perf_counter()-before
    return {'candidates':256,'fast_batch_seconds':fast_seconds,'reference_five_seconds':reference_seconds,
            'warmup_seconds':warmup,'valid_candidates':int(np.count_nonzero(statuses==0)),
            'max_cost_difference_s2':max(errors),'seed':17,'horizon':4,
            'speedup_per_candidate':reference_seconds/5/(fast_seconds/256),
            'provenance':provenance(17,'NumPy default_rng PCG64 Gaussian candidate draws')}


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=profile()
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
