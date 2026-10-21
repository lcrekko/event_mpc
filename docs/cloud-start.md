# Codex cloud startup

Use the existing isolated checkout at `/workspace/event_mpc`; do not create a
Git worktree unless explicitly requested. Work directly on `Solid_first`, and
commit and push every completed change as requested in AGENTS.md.

Read AGENTS.md, CODEX_SETUP.md, README.md and docs/milestone-a.md. Use the local
`.venv/bin/python` (Python 3.12). For dependency refresh run:

```bash
cd /workspace/event_mpc
bash scripts/install-cloud.sh
```

This installs the tested full cloud pins from requirements-cloud.txt and checks
imports, ODE integration, event detection and headless plotting. No persistent
service or credentials are required. Venv and dependencies are retained files;
processes are not assumed to survive cloud publication.

Development validation:

```bash
cd /workspace/event_mpc
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m event_mpc validate
```

All A–E development tests, including independent neuron, hybrid sensing,
predictor, optimizer and causal closed-loop tests, are in the suite. The
separate `validate` command retains Milestone A's 13 numerical checks.
For a new mechanical demonstration,
use `python -m event_mpc run --output outputs/<new-directory>` with the venv
interpreter, then the `metrics` and `plot` commands. Do not overwrite old runs.
Stored evidence lives under results/milestone-a through results/milestone-f;
audit documents are in docs/onboarding. For B–F use docs/milestones-b-f.md,
docs/experiment-plan.md, and results/milestone-f/REPORT.md. Its status table
distinguishes completed and unrun configurations.

Use four candidate threads: `export NUMBA_NUM_THREADS=4` in Bash or
`$env:NUMBA_NUM_THREADS="4"` in PowerShell. For a short controller check:

```bash
.venv/bin/python -m event_mpc.closed_loop --output outputs/<new-directory> --intervals 3 --samples 8
```

To regenerate metrics/figures from the downloaded scientific results without
rerunning numerical integration:

```bash
.venv/bin/python -m event_mpc.report --suite results/milestone-f
```

The declared full suite is `python -m event_mpc.experiments --output outputs/<new-suite>`.
It runs paper-scale CPU workloads and must not be repeated merely as startup.

Latest user-requested two-controller experiment is separately recorded in
configs/startup-comparison.json and results/startup-comparison. It uses initial
theta=[.05,1.5,2], user gain bounds [1.5,2.5] x [1,2], an identical first half-swing,
then uniform seed1 MPC versus fixed control. Old defaults/results are unchanged.
See docs/startup-comparison.md for the timing interpretation and physical metrics.
Regenerate its three publication figures without integration using
`python -m event_mpc.paper_figures --comparison results/startup-comparison` with
the venv interpreter. True LaTeX rendering uses latex and pdftocairo plus native
CM fonts already verified in this cloud machine; explicit --mathtext is the
documented fallback on machines without TeX. Do not rerun parallel benchmarks
merely to explain the old runtime; the existing evaluator already uses threads.

The user explicitly decided to retain exact sine torque (2) and leave printed
(4) unchanged. Both energy diagnostics are implemented; the finite-angle
residual of (4) is reported separately. Do not ask the resolved question again.
Neurons, sensor reconstruction, E2E predictor and MPC are implemented. The user
approved literal objective indices, causal second-detector parameter application,
K=50 main runs plus K=200. Do not repeat those resolved questions. Optimizer wall
time is measured but not injected into simulated delay; no real-time claim is
supported. Read the scientific results before claiming a control advantage.
Windows commands are in README.md;
Windows execution remains unverified. A Linux venv cannot be copied to Windows.

Saving this startup instruction and the installation script to cloud settings
does not itself publish a new cloud snapshot. GitHub publication and cloud
environment publication are separate operations.
