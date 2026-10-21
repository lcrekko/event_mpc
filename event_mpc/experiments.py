"""Run declared Milestone F configurations; postprocess separately with report."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from .closed_loop import run_closed_loop
from .mechanics import MechanicalParameters
from .optimization import SearchSettings

ROOT=Path(__file__).resolve().parents[1]


def run_suite(config,output,only=None,resume=False):
    config=Path(config);output=Path(output);plan=json.loads(config.read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True)
    saved=output/'plan.json'
    if saved.exists():
        if json.loads(saved.read_text(encoding='utf-8'))!=plan:raise ValueError('Existing suite uses a different plan')
    else:saved.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    outcomes=[]
    for spec in plan['runs']:
        if only is not None and spec['name'] not in only:continue
        destination=output/spec['name']
        if destination.exists():
            if resume and (destination/'status.json').exists():
                print('Retaining existing recorded outcome:',spec['name'],flush=True)
                outcomes.append(json.loads((destination/'status.json').read_text()));continue
            raise FileExistsError(f'{destination} exists; preserve incomplete run before retrying')
        search=SearchSettings(horizon=spec.get('horizon',4),samples=spec.get('samples',256),
                              method=spec.get('method','refinement'),
                              constant_parameters=spec.get('constant_parameters',False))
        p=MechanicalParameters()
        plant=replace(p,kappa=p.kappa*spec.get('kappa_factor',1.),
                       damping_ratio=p.damping_ratio*spec.get('damping_factor',1.))
        print('Starting',spec['name'],flush=True)
        outcome=run_closed_loop(destination,spec.get('intervals',50),spec.get('seed',1),
                                search,plant_parameters=plant,description=spec['name'])
        outcomes.append(outcome);print(spec['name'],json.dumps(outcome),flush=True)
    return outcomes


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=ROOT/'configs'/'experiment-suite.json')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--only',nargs='+');p.add_argument('--resume',action='store_true')
    a=p.parse_args();outcomes=run_suite(a.config,a.output,a.only,a.resume)
    # Keep recorded simulation failures separate from runner execution success.
    print('Recorded',len(outcomes),'outcomes; completed',sum(r['status']=='completed' for r in outcomes))
