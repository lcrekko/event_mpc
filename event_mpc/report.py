"""Metrics, scientific report and figures from saved data only (no simulation)."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .mechanics import MechanicalParameters,energy


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def rms(values):
    a=np.asarray(values,dtype=float)
    return float(np.sqrt(np.mean(a*a))) if len(a) else None


def summarize_run(directory):
    d=Path(directory);meta=read(d/'metadata.json');status=read(d/'status.json')
    actions=read(d/'actions.json');records=read(d/'events.json');events=records['events']
    T=meta['objective']['period'];A=meta['objective']['amplitude']
    timing=[e['true_time']-e['event_index']*T for e in events]
    amps=[e['amplitude']-(-1)**(e['event_index']-1)*A for e in events]
    delays=[e['observation']['available_time']-e['true_time'] for e in events]
    sensor_errors=[e['observation']['crossing_time']-e['true_time'] for e in events]
    speed_errors=[abs(e['observation']['omega']-e['true_omega'])/abs(e['true_omega']) for e in events]
    times=np.array([a['optimization_seconds'] for a in actions])
    spacing=np.diff([0.]+[e['true_time'] for e in events])
    ratios=times[:len(spacing)]/spacing if len(spacing) else np.array([])
    with np.load(d/'search.npz') as data:
        codes=data['statuses'];unique,count=np.unique(codes,return_counts=True)
        status_counts={str(int(k)):int(v) for k,v in zip(unique,count)}
        invalid=int(np.count_nonzero(codes!=0));evaluations=len(codes)
    with np.load(d/'trajectory.npz') as data:
        y=data['state'];p=MechanicalParameters(**meta['plant'])
        e=energy(*y[:2],p)
        exact=e-e[0]-y[9]+y[11];paper=e-e[0]-y[10]+y[11]
        max_angle=float(np.max(abs(y[0])))
        final_true=events[-1]['true_time'] if events else 0.
        signed_work=float(np.interp(final_true,data['time'],y[9]))
    return {'name':d.name,'status':status['status'],'completed_intervals':len(events),
            'requested_intervals':meta['intervals'],'seed':meta['seed'],'method':meta['search']['method'],
            'timing_rms_ms':None if not timing else 1e3*rms(timing),
            'last10_timing_rms_ms':None if not timing else 1e3*rms(timing[-10:]),
            'amplitude_rms_deg':None if not amps else float(np.rad2deg(rms(amps))),
            'last10_amplitude_rms_deg':None if not amps else float(np.rad2deg(rms(amps[-10:]))),
            'absolute_work_uJ':1e6*sum(e['absolute_work'] for e in events),
            'signed_work_uJ':1e6*signed_work,'maximum_angle_deg':float(np.rad2deg(max_angle)),
            'exact_energy_relative_residual':float(np.max(abs(exact))/e[0]),
            'equation4_energy_relative_residual':float(np.max(abs(paper))/e[0]),
            'sensor_timestamp_max_error_us':None if not sensor_errors else 1e6*max(abs(v) for v in sensor_errors),
            'sensor_speed_max_relative_error':None if not speed_errors else max(speed_errors),
            'sensor_delay_mean_us':None if not delays else 1e6*float(np.mean(delays)),
            'optimization_median_s':float(np.median(times)) if len(times) else None,
            'optimization_p95_s':float(np.percentile(times,95)) if len(times) else None,
            'optimization_max_s':float(np.max(times)) if len(times) else None,
            'optimization_to_interval_p95':float(np.percentile(ratios,95)) if len(ratios) else None,
            'invalid_candidate_fraction':invalid/evaluations if evaluations else None,
            'candidate_status_counts':status_counts,'evaluations':evaluations,
            'fallback_count':sum(a['fallback'] for a in actions),'wall_seconds':status['wall_seconds']}


def render_figures(suite,rows):
    import os
    os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures=suite/'figures';figures.mkdir(exist_ok=True)
    colors=plt.rcParams['axes.prop_cycle'].by_key()['color']
    names=['nominal-seed1','fixed-nominal','uniform-seed1','constant-seed1']
    fig,ax=plt.subplots(3,1,figsize=(10,9),sharex=True)
    for i,name in enumerate(names):
        d=suite/name
        if not (d/'status.json').exists():continue
        events=read(d/'events.json')['events'];meta=read(d/'metadata.json');T=meta['objective']['period']
        k=np.array([e['event_index'] for e in events]);t=np.array([e['true_time'] for e in events])
        amp=np.rad2deg([abs(e['amplitude']) for e in events])
        act=read(d/'actions.json')
        ax[0].plot(k,(t-k*T)*1e3,label=name,color=colors[i])
        ax[1].plot(k,amp,label=name,color=colors[i])
        ax[2].plot(np.arange(1,len(act)+1),[a['optimization_seconds'] for a in act],label=name,color=colors[i])
    ax[0].set_ylabel('Crossing error [ms]');ax[0].legend()
    ax[1].axhline(5,color='black',ls='--',lw=1);ax[1].set_ylabel('Half-swing magnitude [deg]')
    ax[2].axhline(.05,color='black',ls='--',lw=1,label='Nominal interval')
    ax[2].set_ylabel('Optimization wall time [s]');ax[2].set_xlabel('Event index')
    fig.suptitle('Causal sensor feedback; optimizer time excluded from simulated delay')
    fig.tight_layout();fig.savefig(figures/'comparison.png',dpi=160);plt.close(fig)

    names=[r['name'] for r in rows]
    fig,ax=plt.subplots(3,1,figsize=(12,10),sharex=True)
    for axis,key,label in zip(ax,['timing_rms_ms','amplitude_rms_deg','absolute_work_uJ'],
                              ['Timing RMS [ms]','Extremum RMS [deg]','Absolute work [microJ]']):
        axis.bar(np.arange(len(rows)),[np.nan if r[key] is None else r[key] for r in rows]);axis.set_ylabel(label)
    ax[-1].set_xticks(np.arange(len(rows)),names,rotation=45,ha='right')
    fig.suptitle('All recorded runs (see report for completion status)');fig.tight_layout()
    fig.savefig(figures/'all-runs.png',dpi=160);plt.close(fig)

    d=suite/'nominal-seed1'
    if (d/'status.json').exists():
        act=read(d/'actions.json');events=read(d/'events.json')['events']
        fig,axes=plt.subplots(4,1,figsize=(10,10),sharex=True)
        theta=np.array([a['theta'] for a in act]);t=[a['applied_time'] for a in act]
        for j,label in enumerate(['Current amplitude [mA]','Slow gain','Ultraslow gain']):
            axes[j].step(t,theta[:,j]*(1000 if j==0 else 1),where='post');axes[j].set_ylabel(label)
        with np.load(d/'trajectory.npz') as data:
            axes[3].plot(data['time'],np.rad2deg(data['state'][0]),lw=.8)
        axes[3].set_ylabel('Mirror angle [deg]');axes[3].set_xlabel('Time [s]')
        fig.suptitle('Nominal seed 1: parameter evolution and raw trajectory');fig.tight_layout()
        fig.savefig(figures/'nominal-parameters.png',dpi=160);plt.close(fig)

    long=suite/'long-200'
    if (long/'status.json').exists():
        events=read(long/'events.json')['events'];k=np.array([e['event_index'] for e in events])
        fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
        axes[0].plot(k,1e3*(np.array([e['true_time'] for e in events])-k*.05));axes[0].set_ylabel('Crossing error [ms]')
        axes[1].plot(k,np.rad2deg([abs(e['amplitude']) for e in events]));axes[1].axhline(5,color='black',ls='--')
        axes[1].set_ylabel('Magnitude [deg]');axes[1].set_xlabel('Event index')
        fig.suptitle('K=200 alternative');fig.tight_layout();fig.savefig(figures/'long-run.png',dpi=160);plt.close(fig)
    # Independent B/C evidence is rendered from its saved raw data, too.
    root=suite.parent
    if (root/'milestone-b'/'neurons.npz').exists():
        with np.load(root/'milestone-b'/'neurons.npz') as data:
            fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
            for i,label in enumerate(['A','B']):
                axes[0].plot(data['time'],data['state'][i*3],label=label)
                axes[1].plot(data['time'],data['state'][i*3+1],label=label+' slow')
            axes[0].axhline(0,color='black',ls='--');axes[0].legend();axes[1].legend()
            axes[0].set_ylabel('Fast voltage');axes[1].set_ylabel('Slow voltage');axes[1].set_xlabel('Time [s]')
            fig.tight_layout();fig.savefig(figures/'neurons.png',dpi=160);plt.close(fig)
    if (root/'milestone-c'/'coupled.npz').exists():
        observations=read(root/'milestone-c'/'sensing.json')['observations']
        detectors=read(root/'milestone-c'/'sensing.json')['detector_events']
        with np.load(root/'milestone-c'/'coupled.npz') as data:
            fig,axes=plt.subplots(3,1,figsize=(10,8))
            axes[0].plot(data['time'],np.rad2deg(data['state'][0]));axes[0].set_ylabel('Mirror angle [deg]')
            axes[0].set_xlabel('Time [s]')
            if observations:
                center=observations[0]['true_time'];mask=abs(data['time']-center)<.0005
                axes[1].plot(data['time'][mask],np.rad2deg(data['state'][0,mask]))
                for detector in detectors:
                    if abs(detector['time']-center)<.0005:
                        axes[1].axvline(detector['time'],ls='--',label=detector['detector'])
                axes[1].axvline(center,color='black',label='Physical crossing')
                axes[1].axvline(observations[0]['available_time'],color='red',ls=':',label='Feedback available')
                axes[1].set_ylabel('Mirror angle [deg]');axes[1].set_xlabel('Time [s]');axes[1].legend()
                axes[2].plot(np.arange(1,len(observations)+1),
                              [o['omega']-o['true_omega'] for o in observations],marker='o')
                axes[2].set_ylabel('Speed estimate error [rad/s]');axes[2].set_xlabel('Passage index')
            fig.suptitle('Detector reconstruction and causal availability');fig.tight_layout()
            fig.savefig(figures/'sensing.png',dpi=160);plt.close(fig)
    if (suite/'nominal-seed1'/'search.npz').exists():
        d=suite/'nominal-seed1';indices=[x for x in read(d/'search-index.json') if x['event_index']==0]
        with np.load(d/'search.npz') as data:
            minima=[];medians=[]
            for entry in indices:
                c=data['costs'][entry['offset']:entry['offset']+entry['count']]
                finite=c[np.isfinite(c)];minima.append(np.min(finite)*1e6);medians.append(np.median(finite)*1e6)
        fig,ax=plt.subplots(figsize=(8,4));k=np.arange(len(indices))
        ax.plot(k,minima,'o-',label='Minimum valid cost');ax.plot(k,medians,'s--',label='Median valid cost')
        ax.set_xticks(k,[x['label'] for x in indices]);ax.set_ylabel('Predicted objective [ms squared]')
        ax.set_title('First nominal optimization: candidates and evaluated means');ax.legend();fig.tight_layout()
        fig.savefig(figures/'optimizer-history.png',dpi=160);plt.close(fig)


def make_report(suite,allow_incomplete=False):
    suite=Path(suite);plan=read(suite/'plan.json');rows=[];missing=[]
    for spec in plan['runs']:
        d=suite/spec['name']
        if not (d/'status.json').exists():missing.append(spec['name']);continue
        row=summarize_run(d);rows.append(row)
        (d/'metrics.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    grouped={}
    for group in ['nominal','uniform']:
        selected=[r for r in rows if r['name'].startswith(group+'-seed')]
        if selected:
            grouped[group]={'recorded_runs':len(selected),'completed_runs':sum(r['status']=='completed' for r in selected)}
            for key in ['timing_rms_ms','amplitude_rms_deg','absolute_work_uJ','optimization_median_s']:
                values=[r[key] for r in selected if r[key] is not None]
                grouped[group][key]={'mean':float(np.mean(values)),'std_sample':float(np.std(values,ddof=1)) if len(values)>1 else None}
    summary={'runs':rows,'groups':grouped,'unrun':missing}
    (suite/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    scalar_keys=[k for k,v in rows[0].items() if not isinstance(v,dict)] if rows else []
    with (suite/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=scalar_keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    lines=['# Milestone F simulation results','',
           'Generated from saved raw data; no model integration occurs during reporting.',
           'Settings and hypotheses: [experiment plan](../../docs/experiment-plan.md).','',
           '| Run | Status / intervals | Timing RMS (ms) | Extrema RMS (deg) | Abs. work (microJ) | Median / p95 optimization (s) | Invalid candidates |',
           '|---|---|---:|---:|---:|---:|---:|']
    def fmt(v):return 'n/a' if v is None else f'{v:.5g}'
    for r in rows:
        lines.append(f"| {r['name']} | {r['status']} {r['completed_intervals']}/{r['requested_intervals']} | {fmt(r['timing_rms_ms'])} | {fmt(r['amplitude_rms_deg'])} | {fmt(r['absolute_work_uJ'])} | {fmt(r['optimization_median_s'])} / {fmt(r['optimization_p95_s'])} | {fmt(r['invalid_candidate_fraction'])} |")
    lines+=['','## Interpretation and limits','',
            'These results use literal (13), including its missing terminal timing penalty, and causal sensor availability. Optimization execution time is measured but not injected into simulated actuation delay. Compute-time ratios above one violate a one-interval execution budget on this machine; no real-time claim is supported.',
            'Three-seed summaries report descriptive sample variation, not statistical significance. Mismatch and sensitivity magnitudes are declared evaluation choices; they do not prove robustness beyond these tested cases. Fixed and optimized HCO results must be compared across timing, amplitude and energy together; lower energy alone need not mean better tracking.',
            'All statuses are retained. Metrics for truncated runs describe only their completed prefix and must not be presented as full-horizon success. The final-ten metrics are a descriptive tail window, not a proven steady state. Printed equation (4) is unchanged; exact and printed energy residuals are separate fields.',
            'All candidate costs/statuses, configurations, detector and action histories, raw trajectories, seeds and original source provenance remain in the run directories. Runtime varies by machine and includes optimization work after a separately recorded JIT warmup. Windows execution remains untested.',
            '',f"Unrun configurations: {', '.join(missing) if missing else 'none'}.",'',
            '## Figures','',
            '![Comparison](figures/comparison.png)','',
            '![All runs](figures/all-runs.png)','',
            '![Parameters](figures/nominal-parameters.png)','',
            '![Long run](figures/long-run.png)','',
            '![Neurons](figures/neurons.png)','']
    lines+=['![Sensing](figures/sensing.png)','','![Optimizer](figures/optimizer-history.png)','']
    findings=['## Numerical findings','']
    baseline=next((r for r in rows if r['name']=='fixed-nominal'),None)
    if baseline and 'nominal' in grouped:
        g=grouped['nominal']
        findings.append(f"Across {g['recorded_runs']} nominal seeds, mean timing RMS is {g['timing_rms_ms']['mean']:.6g} ms and mean extremum RMS is {g['amplitude_rms_deg']['mean']:.6g} deg. Fixed nominal parameters give {baseline['timing_rms_ms']:.6g} ms and {baseline['amplitude_rms_deg']:.6g} deg. The nominal initialization is already close to the desired periodic orbit; these comparisons do not demonstrate a tracking advantage for MPC.")
        findings.append(f"Mean nominal MPC absolute work is {g['absolute_work_uJ']['mean']:.6g} microJ versus fixed {baseline['absolute_work_uJ']:.6g} microJ. This is a mechanical-work comparison, not electrical consumption.")
    for group,g in grouped.items():
        findings.append(f"{group}: {g['completed_runs']}/{g['recorded_runs']} completed runs. Timing RMS mean/sample SD = {g['timing_rms_ms']['mean']:.6g} / {fmt(g['timing_rms_ms']['std_sample'])} ms; extrema RMS = {g['amplitude_rms_deg']['mean']:.6g} / {fmt(g['amplitude_rms_deg']['std_sample'])} deg.")
    nonfixed=[r for r in rows if r['method']!='fixed' and r['optimization_to_interval_p95'] is not None]
    if nonfixed:
        findings.append(f"Across nonfixed recorded runs, p95 optimization/event-duration ratios range from {min(r['optimization_to_interval_p95'] for r in nonfixed):.4g} to {max(r['optimization_to_interval_p95'] for r in nonfixed):.4g}. A ratio over one rules out one-event computation on this tested setup without further changes. Fixed-baseline timing includes one logged nominal forecast, not a search.")
    audit_path=suite/'forecast-audit.json'
    if audit_path.exists():
        audit=read(audit_path);errors=audit.get('one_step_forecast_errors',[])
        if errors:
            findings.append(f"Frozen nominal seed1 selected sequences passed independent/refined solver checks: {audit['passed']}. Across {len(errors)} one-step forecasts, maximum predicted-versus-plant crossing error is {max(abs(e['first_crossing_error_s']) for e in errors):.6g} s and extremum error {max(abs(e['first_extremum_error_rad']) for e in errors):.6g} rad. These are much smaller than the reported control errors; the observed tracking behavior cannot be presented as solver convergence failure. See [audit](forecast-audit.json).")
    findings+=['',f"Recorded closed-loop failures: {sum(r['status']!='completed' for r in rows)}. Total fallbacks: {sum(r['fallback_count'] for r in rows)}. Unrun: {len(missing)}.",'']
    insertion=lines.index('## Interpretation and limits')
    lines[insertion:insertion]=findings
    (suite/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    render_figures(suite,rows)
    if missing and not allow_incomplete:raise RuntimeError('Unrun configurations: '+', '.join(missing))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
    summary=make_report(a.suite,a.allow_incomplete)
    print('Reported',len(summary['runs']),'runs; unrun',len(summary['unrun']))
