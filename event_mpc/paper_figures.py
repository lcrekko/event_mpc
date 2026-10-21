"""Three publication figures from saved two-controller data; no integration."""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
from .mechanics import MechanicalParameters,torque
from .report import read,summarize_run

ROOT=Path(__file__).resolve().parents[1]


def performance_series(run):
    run=Path(run);meta=read(run/'metadata.json');events=read(run/'events.json')['events']
    t=np.array([e['true_time'] for e in events])
    return {'time':t,'amplitude':np.rad2deg([abs(e['amplitude']) for e in events]),
            'timing_error':1000*(t-np.array([e['event_index'] for e in events])*meta['objective']['period']),
            'work':1e6*np.array([e['absolute_work'] for e in events])}


def actuation_series(run):
    """Reconstruct exact (2)/(6), using logged right-continuous pulse branches."""
    run=Path(run);meta=read(run/'metadata.json');actions=read(run/'actions.json')
    records=read(run/'events.json');end=records['events'][-1]['true_time']
    with np.load(run/'trajectory.npz') as data:
        mask=data['time']<=end;time=data['time'][mask].copy();state=data['state'][:,mask].copy()
    at=np.array([a['applied_time'] for a in actions]);theta=np.array([a['theta'] for a in actions])
    ai=np.maximum(0,np.searchsorted(at,time,side='right')-1)
    switches=records['switches'];st=np.array([s['time'] for s in switches])
    flags=np.array([meta['initial_state'][2]>=meta['neurons']['threshold']]+[s['active'] for s in switches])
    active=flags[np.searchsorted(st,time,side='right')]
    current=theta[ai,0]*active
    p=MechanicalParameters(**meta['plant'])
    return {'time':time,'torque':torque(state[0],current,p),'fast_voltage':state[2],
            'current':current,'application_times':at,'parameters':theta,'end':end}


def configure_style(tex):
    # Native LaTeX serif is Computer Modern Roman. Selecting its generic name
    # avoids requiring EC-encoded fonts/type1ec, while leaving font verification on.
    return {'text.usetex':tex,'font.family':'serif',
            'font.serif':['serif'] if tex else ['DejaVu Serif'],
            'font.sans-serif':['sans-serif'] if tex else ['DejaVu Sans'],
            'font.monospace':['Courier'] if tex else ['DejaVu Sans Mono'],
            'mathtext.fontset':'cm','font.size':11,'axes.labelsize':11,
            'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':11,
            'axes.linewidth':.65,'lines.linewidth':1.35,'lines.markersize':2.4,
            'xtick.direction':'in','ytick.direction':'in','xtick.major.width':.65,
            'ytick.major.width':.65,'savefig.dpi':600,'path.simplify':False,
            'pdf.fonttype':42,'svg.fonttype':'path','axes.unicode_minus':False}


def render(comparison,tex=True,width_inches=4.5):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    comparison=Path(comparison);out=comparison/'figures';out.mkdir(exist_ok=True)
    if tex and (shutil.which('latex') is None or shutil.which('pdftocairo') is None):
        raise RuntimeError('LaTeX rendering needs latex and pdftocairo; install them or explicitly use --mathtext')
    mpc=comparison/'ec-mpc';fixed=comparison/'nominal-control'
    for d in (mpc,fixed):
        status=read(d/'status.json')
        if status['status']!='completed':raise ValueError('Figure input did not complete: '+str(d))
    series=[performance_series(mpc),performance_series(fixed)];act=actuation_series(mpc)
    colors=['#0072B2','#D55E00'];labels=['EC-MPC','Nominal Control'];styles=['-','--']
    parameter_colors=['#0072B2','#D55E00','#009E73']
    actuation_colors=['#0072B2','#8B5FBF']
    layouts={}
    if not np.isfinite(width_inches) or width_inches<3.5:
        raise ValueError('Figure width must be finite and at least 3.5 inches')
    with plt.rc_context(configure_style(tex)):
        def stack(rows,legend=False):
            # Physical dimensions set the plotting boxes, not just the canvas.
            left,right,bottom,gap=.90,.10,.43,.08
            top=.36 if legend else .10
            plot_width=width_inches-left-right
            plot_height=plot_width/4
            height=bottom+rows*plot_height+(rows-1)*gap+top
            fig=plt.figure(figsize=(width_inches,height));axes=[]
            for i in range(rows):
                y=bottom+(rows-1-i)*(plot_height+gap)
                ax=fig.add_axes([left/width_inches,y/height,plot_width/width_inches,plot_height/height],
                                sharex=axes[0] if axes else None)
                ax.set_box_aspect(.25)
                ax.tick_params(labelbottom=i==rows-1)
                axes.append(ax)
            return fig,axes
        def finish(fig,axes,stem,legend=False):
            for ax in axes:
                ax.spines[['top','right']].set_visible(False)
                ax.tick_params(pad=3)
                ax.set_facecolor('#F3F3F3')
                ax.set_axisbelow(True)
                ax.grid(axis='both',color='white',linestyle='--',linewidth=.7)
                ax.margins(y=.20)
            axes[-1].set_xlabel(r'$t\,[\mathrm{s}]$')
            fig.align_ylabels(axes)
            fig.savefig(out/(stem+'.pdf'))
            boxes=[]
            for ax in axes:
                position=ax.get_position()
                w=position.width*fig.get_figwidth();h=position.height*fig.get_figheight()
                if not np.isclose(h/w,.25,atol=1e-12,rtol=0):
                    raise RuntimeError('Exported plotting box does not have height:width 1:4')
                boxes.append({'width_inches':w,'height_inches':h,'height_over_width':h/w,
                              'ylabel':ax.get_ylabel()})
            layouts[stem]={'figure_inches':list(fig.get_size_inches()),'axes':boxes,
                           'subplot_gap_inches':.08}
            fig.savefig(out/(stem+'.svg'))
            svg=out/(stem+'.svg')
            # Matplotlib emits trailing spaces in SVG path attributes; normalize
            # line endings while retaining every path command/coordinate.
            svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                           encoding='utf-8')
            if tex:
                # PDF rasterization preserves the same verified TeX glyphs, and
                # does not require Matplotlib's separate dvipng executable.
                subprocess.run(['pdftocairo','-png','-singlefile','-r','600',str(out/(stem+'.pdf')),
                                str(out/stem)],check=True,capture_output=True)
            else:fig.savefig(out/(stem+'.png'),dpi=600)
            plt.close(fig)

        fig,axes=stack(3,legend=True)
        for s,color,label,style in zip(series,colors,labels,styles):
            for ax,key in zip(axes,['amplitude','timing_error','work']):
                ax.plot(s['time'],s[key],style,color=color,label=label)
        axes[0].axhline(5.,color='.35',ls=':',lw=.8)
        axes[1].axhline(0.,color='.35',ls=':',lw=.8)
        axes[1].yaxis.set_major_locator(MultipleLocator(10))
        axes[2].yaxis.set_major_locator(MultipleLocator(.1))
        axes[0].set_ylim(0,max(6.,max(float(np.max(s['amplitude'])) for s in series)*1.2))
        axes[2].set_ylim(0,max(float(np.max(s['work'])) for s in series)*1.3)
        for ax,label in zip(axes,[r'$|A|\,[\mathrm{deg}]$',
                                 r'$t_{\mathrm{M}}-t^{\ast}_{\mathrm{M}}\;[\mathrm{ms}]$',
                                 r'$q\,[\mu\mathrm{J}]$']):
            ax.set_ylabel(label)
        axes[-1].set_xlim(0,max(s['time'][-1] for s in series))
        fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.57,1.),
                   ncol=2,frameon=False,columnspacing=1.,handlelength=1.5,handletextpad=.45)
        finish(fig,axes,'figure1-performance',legend=True)

        fig,axes=stack(3)
        t=np.r_[act['application_times'],act['end']]
        theta=np.vstack([act['parameters'],act['parameters'][-1]])
        for j,(ax,label) in enumerate(zip(axes,[r'$I_0\,[\mathrm{mA}]$',r'$g^{-}_{\mathrm{s}}$',r'$g^{+}_{\mathrm{us}}$'])):
            ax.step(t,theta[:,j]*(1000 if j==0 else 1),where='post',color=parameter_colors[j]);ax.set_ylabel(label)
        axes[-1].set_xlim(0,act['end'])
        finish(fig,axes,'figure2-parameters')

        fig,axes=stack(2)
        axes[0].plot(act['time'],act['torque']*1e6,color=actuation_colors[0],lw=.8)
        axes[1].plot(act['time'],act['fast_voltage'],color=actuation_colors[1],lw=.8)
        axes[0].set_ylabel(r'$\tau\,[\mu\mathrm{N\,m}]$')
        axes[1].set_ylabel(r'$\nu_{\mathrm{f},n_{A}}$')
        axes[0].yaxis.set_major_locator(MultipleLocator(5))
        axes[1].yaxis.set_major_locator(MultipleLocator(2))
        axes[1].axhline(0,color='.35',ls=':',lw=.7);axes[-1].set_xlim(0,act['end'])
        finish(fig,axes,'figure3-actuation')

    # Export the plotted performance coordinates for transparent reuse.
    with (comparison/'performance.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['controller','time_s','amplitude_deg','crossing_error_ms','absolute_work_uJ'])
        for label,s in zip(labels,series):
            writer.writerows((label,*row) for row in zip(s['time'],s['amplitude'],s['timing_error'],s['work']))
    rows={name:summarize_run(comparison/name) for name in ['ec-mpc','nominal-control']}
    for name,row in rows.items():
        (comparison/name/'metrics.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    from .__main__ import provenance
    rendering={'text_usetex':tex,'font':'Computer Modern Roman (native LaTeX serif)' if tex else 'DejaVu Serif + CM mathtext',
               'figure_size_inches':{f'figure{i}':layouts[stem]['figure_inches'] for i,stem in
                   enumerate(['figure1-performance','figure2-parameters','figure3-actuation'],1)},
               'layout':layouts,'plot_height_over_width':.25,
               'parameter_colors':parameter_colors,'actuation_colors':actuation_colors,'grid':'both',
               'tick_font_pt':10,'axis_label_pt':11,'legend_pt':11,'png_dpi':600,
               'formats':['PDF','SVG','PNG'],'metrics':rows,'provenance':provenance()}
    (comparison/'rendering.json').write_text(json.dumps(rendering,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return rendering


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--comparison',type=Path,required=True)
    p.add_argument('--mathtext',action='store_true',help='Explicit non-LaTeX option for machines without a TeX installation')
    p.add_argument('--width-inches',type=float,default=4.5,help='Canvas width; each plotting box retains height:width 1:4')
    a=p.parse_args();r=render(a.comparison,tex=not a.mathtext,width_inches=a.width_inches)
    print(json.dumps(r['metrics'],indent=2))
