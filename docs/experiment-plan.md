# Milestone F: declared experiment plan

The user approved causal second-detector application, literal objective indices,
K=50 main runs and an additional K=200 run. The following experiment choices
are explicit engineering evaluation configurations, not missing manuscript text.
No reference or physical parameter is silently fitted to obtain good outcomes.
Nominal values use Tables I–III/(25)–(30) as in previous milestones.

## Questions and comparisons, declared before execution

1. Does full EC-MPC maintain the desired 50ms half-period / signed 5-degree
   extrema under sparse causal feedback? Run N=4,M=256,R=2 for 50 intervals,
   seeds 1,2,3. Report all event-time/amplitude errors, effort and failures.
2. Does optimization improve over the nominal fixed HCO? Use the same plant,
   initial conditions, solver and references. Fixed HCO has no search budget;
   compare control outcomes rather than calling it equal computation.
3. Compare projected Gaussian refinement with uniform random shooting from
   Remark 4. Uniform uses 514 evaluations per event to match refinement's
   2*256+2 evaluated means; both use seeds 1,2,3. Their sampling distributions
   intentionally differ. Random draws and statuses are saved, including invalids.
4. Compare constant-horizon parameters (Remark 1) with the full sequence, seed1,
   same 514 evaluations. This is a dimension reduction, not identical candidates.
5. Run the Table III interpretation K=200, seed1, without changing settings.
6. Test plant-only kappa+10% and damping+25%, seed1. Predictor retains nominal
   parameters, controller receives no mechanical truth. These mismatch amounts
   are evaluation choices, not uncertainty bounds or a robustness guarantee.
7. Budget sensitivity M=64 (130 evaluations) and horizon sensitivity N=2 with
   other nominal settings unchanged, seed1. Report computation/error tradeoffs.

All full runs use the .1s event timeout, angle limit 10 degrees, parameter bounds
from the paper, max step 87.315 microseconds and stated adaptive component
tolerances. Four CPU threads evaluate candidates; RNG draws are serial before
parallel numerical work. CPU quota is four cores, memory limit 32GiB.

## Metrics, reliability checks and limits

Report all-run and final-ten-interval RMS event-time errors, signed-extremum
errors, total absolute mechanical work, actual signed work, mechanical energy
balance, invalid candidate fraction by status, fallback count, completed/requested
intervals, and optimization median/95th percentile/max wall time divided by
actual event spacing. Distinguish sensor reconstruction error, sensor delay
and computation time. Objective (13) is in s² and has no terminal timing term.

Closed-loop **performance has no pre-assumed passing threshold**. Report actual
outcomes and whether comparisons improve or worsen metrics; preserve failed
and truncated runs in aggregates. The existing 26 numerical/unit tests and
backend accuracy bounds establish implementation checks, not control performance.
Three seeds demonstrate variability, not a statistical significance claim.

Additional frozen selected-sequence convergence checks at nominal seed1 events
0,25,49 compare fast default, halved step/rtol=1e-9, and independent SciPy
reference. Use the same predeclared backend acceptance bounds as Milestone E.
No candidate reselection or retuning is used to make this check pass.

Solver trajectories, detector events, reconstructed observations, true states
for validation, current parameter actions, every sampled/mean candidate with
its cost/status, RNG seed, solver settings, software/source provenance and run
status are saved. `report` consumes saved data and generates metrics/figures
without rerunning simulations. The manuscript PDF remains unchanged; findings
are written as a separate simulation report.

Sensor availability is implemented causally. Optimization wall time is measured
but **not added to simulated actuation time**. No measured runtime is claimed as
a real-time guarantee. The paper's zero-computation-delay idealization may be
unrealistic if optimization time exceeds the event interval; report this plainly.
No free-period experiment is invented, since no complete formulation is supplied.

## Commands

From repository root, prefix python with the project-local interpreter:

```
python -m event_mpc.experiments --output results/milestone-f
python -m event_mpc.report --suite results/milestone-f
```

For interrupted execution, `--resume` retains recorded outcomes, including
failures; it refuses to silently overwrite partial directories. `--only NAME`
runs a declared subset. On PowerShell use `$env:NUMBA_NUM_THREADS="4"`;
on Linux `NUMBA_NUM_THREADS=4 .venv/bin/python ...`.
