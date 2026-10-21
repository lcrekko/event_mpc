# Event-centric scanning-mirror MPC

Milestones A–E implement mechanics, neurons, hybrid actuation, sparse sensing,
event prediction and causal EC-MPC. Milestone F runs the declared comparisons,
sensitivity and mismatch experiments.
The manuscript is in `paper/`; scientific scope is described in AGENTS.md and
CODEX_SETUP.md. See [model and validation conventions](docs/milestone-a.md).

For B–F see [implementation/validation decisions](docs/milestones-b-f.md),
[experiment plan](docs/experiment-plan.md), and the
[saved scientific report](results/milestone-f/REPORT.md). A Chinese
[getting-started guide](docs/使用指南.md) explains the cloud/GitHub/local workflow.
The report records completed and unrun configurations explicitly while a suite
is running; use its status table, not the presence of a directory, as evidence.

The initial [manuscript audit](docs/onboarding/specification-audit.md),
[open questions](docs/onboarding/open-questions.md), and
[milestone plan](docs/onboarding/milestone-plan.md) are now included in this
repository. Previously they existed only in the Codex cloud workspace.
Saved Milestone A [validation](results/milestone-a/validation.json),
[figure](results/milestone-a/demo/mechanical.png) and
[raw data](results/milestone-a/demo/trajectory.npz) are included under `results/`.
New exploratory runs remain ignored under `outputs/`; selected evidence is
copied to `results/` for GitHub publication. Historical metadata preserves the
original uncommitted-run provenance and has not been rewritten.

## Windows PowerShell / VS Code

From the repository root, using Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m event_mpc validate --output validation.json
.\.venv\Scripts\python.exe -m event_mpc run --output outputs/demo-a
.\.venv\Scripts\python.exe -m event_mpc metrics outputs/demo-a
.\.venv\Scripts\python.exe -m event_mpc plot outputs/demo-a
```

In VS Code use **Python: Select Interpreter** and choose
`.venv\Scripts\python.exe`. Activation and execution-policy changes are not
required. Windows execution has not been tested in this Linux cloud machine.
Each new simulation needs a new output directory; existing runs are never
overwritten. Omit `--output` for a timestamped directory. Use a new validation
filename on repeated validation, or omit that option to print the report only.

## Cloud / Linux

The prepared `.venv` already contains the dependencies. From the repository root:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m event_mpc validate
.venv/bin/python -m event_mpc run --output outputs/demo-a
.venv/bin/python -m event_mpc metrics outputs/demo-a
.venv/bin/python -m event_mpc plot outputs/demo-a
```

For a fresh Linux environment: `python3.12 -m venv .venv`, then
`.venv/bin/python -m pip install -r requirements.txt`. Do not copy a Linux venv
to Windows. Requirements pin direct dependencies; complete cloud dependency
versions are also recorded in `requirements-cloud.txt`. These full pins describe
the tested Linux environment; use `requirements.txt` for the Windows workflow.

Regenerate the saved demonstration figure from downloaded data without rerunning
the simulation:

```powershell
.\.venv\Scripts\python.exe -m event_mpc plot results/milestone-a/demo
```

Cloud setup instructions are versioned in `scripts/install-cloud.sh` and
`docs/cloud-start.md`. [The work record](docs/work-record.md) explains what was
completed, saved and published. Work is committed directly to `Solid_first`
and pushed after each completed change, as requested.

Run a short MPC example on Windows (then use new directories for later runs):

```powershell
$env:NUMBA_NUM_THREADS="4"
.\.venv\Scripts\python.exe -m event_mpc.closed_loop --output outputs/mpc-debug --intervals 3 --samples 8
```

For the declared full experiment suite and saved-data report:

```powershell
.\.venv\Scripts\python.exe -m event_mpc.experiments --output outputs/full-suite
.\.venv\Scripts\python.exe -m event_mpc.report --suite outputs/full-suite
```

The full suite costs substantially more CPU time than the short example. Initial
Numba compilation takes extra time; subsequent numerical evaluation is compiled.
Sensor delay is causal, but measured optimizer time is not added to simulated
actuation delay. These results are not a real-time implementation claim.

`event_mpc/mechanics.py` contains reusable mechanics/integration,
`metrics.py` postprocessing, `validation.py` numerical checks, and `__main__.py`
the mechanical run/metrics/plot/validate commands. `neurons.py`, `coupled.py`,
`sensing.py`, `prediction.py`, `objective.py`, `optimization.py` and `closed_loop.py`
separate the controller workflow; `fast_prediction.py` is checked against the
independent SciPy reference. `experiments.py` runs configurations; `report.py`
processes saved results and plots without integration.
`configs/mechanical_demo.json` is explicitly a demonstration configuration;
the full experiment plan is separately declared in `configs/experiment-suite.json`.

The exact torque (2) is used. Printed energy equation (4) is retained unchanged
as a separate diagnostic. Its finite-angle discrepancy with the exact dynamics
is reported explicitly. The manuscript PDF is unchanged.
