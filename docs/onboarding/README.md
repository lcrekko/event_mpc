# Event MPC environment and initial audit

Historical onboarding report, copied into Git for publication. Paths below
describe the original cloud run. For current portable commands use the
repository [README](../../README.md); the full cloud pins are now also at
`requirements-cloud.txt` in the repository root. Subsequent Milestone A work
is documented in [the results](../milestone-a-results.md).

Inspected repository `lcrekko/event_mpc`, branch `Solid_first`, commit `f732082dbc1a7ca5149ed37290d8e3d1f5420462`: AGENTS.md, CODEX_SETUP.md, and all seven manuscript pages, including figures/captions and tables. No simulation code, dependency manifest, CI or tests exist yet. Repository files are unchanged. Setup documents live outside the checkout to respect onboarding restrictions.

Python 3.12.14; project-local `/workspace/event_mpc/.venv`. Minimal numerical stack: NumPy 2.3.5 (arrays/random sampling), SciPy 1.17.0 (integration/events), Matplotlib 3.10.8 (figures without LaTeX). No GPU, database, service or secrets required. All transitive versions are recorded in requirements-cloud.txt. No notebooks, pandas or optimization packages are currently needed.

Verified: isolated imports; SciPy adaptive integration of y'=-y against analytical value and detected half-value event; Matplotlib headless PNG generation; dependency compatibility. This is an environment smoke check, not validation of manuscript equations or a simulation implementation. Windows has not been tested on this Linux cloud machine.

Cloud checks:
```bash
cd /workspace/event_mpc
XDG_CACHE_HOME=/workspace/.cache MPLCONFIGDIR=/workspace/.cache/matplotlib .venv/bin/python /workspace/event_mpc-onboarding/verify.py
UV_CACHE_DIR=/workspace/.cache/uv uv pip check --python .venv/bin/python
```

Windows PowerShell (from your local repository, Python 3.12 installed):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy==2.3.5 scipy==1.17.0 matplotlib==3.10.8
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import numpy, scipy, matplotlib; from scipy.integrate import solve_ivp; print(numpy.__version__, scipy.__version__, matplotlib.__version__)"
```
Activation is optional; explicit interpreter paths avoid PowerShell execution-policy changes. In VS Code install the Python extension, then Ctrl+Shift+P → Python: Select Interpreter → select `.venv\Scripts\python.exe`. Recreate the venv locally; a Linux venv cannot be copied to Windows. Cloud transitive pins are recorded separately; Windows wheel compatibility remains to be verified.

See specification-audit.md, open-questions.md and milestone-plan.md. Environment is ready for development. Milestone A numerical work awaits the energy-law clarification.
