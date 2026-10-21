"""Reproduce the user's fixed-versus-uniform comparison; render separately."""
import argparse
import json
from pathlib import Path
from .closed_loop import run_closed_loop
from .optimization import SearchSettings

ROOT=Path(__file__).resolve().parents[1]


def run_comparison(output,config=None):
    config=ROOT/'configs'/'startup-comparison.json' if config is None else Path(config)
    plan=json.loads(config.read_text(encoding='utf-8'));output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    saved=output/'plan.json'
    if saved.exists() and json.loads(saved.read_text(encoding='utf-8'))!=plan:
        raise ValueError('Existing comparison has a different plan')
    saved.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    outcomes={}
    for name,method,startup in [('nominal-control','fixed',0),('ec-mpc','uniform',plan['mpc_startup_intervals'])]:
        path=output/name
        if (path/'status.json').exists():
            meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
            if (meta.get('initial_theta')!=plan['initial_theta'] or meta['seed']!=plan['seed']
                    or meta['intervals']!=plan['intervals'] or meta['search']['method']!=method
                    or meta['startup_intervals']!=startup
                    or meta['search'].get('lower')!=plan['search_lower']
                    or meta['search'].get('upper')!=plan['search_upper']):
                raise ValueError('Existing run does not match comparison configuration')
            outcomes[name]=json.loads((path/'status.json').read_text());continue
        outcomes[name]=run_closed_loop(path,plan['intervals'],plan['seed'],
            SearchSettings(method=method,samples=plan['samples'],horizon=plan['horizon'],
                           lower=tuple(plan['search_lower']),upper=tuple(plan['search_upper'])),
            initial_theta=plan['initial_theta'],startup_intervals=startup,description=plan['purpose'])
    return outcomes


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path);a=p.parse_args();r=run_comparison(a.output,a.config)
    print(json.dumps(r,indent=2));raise SystemExit(0 if all(v['status']=='completed' for v in r.values()) else 1)
