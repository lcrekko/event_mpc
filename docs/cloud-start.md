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

Expect 8 tests and 13 numerical checks at Milestone A. For a new demonstration,
use `python -m event_mpc run --output outputs/<new-directory>` with the venv
interpreter, then the `metrics` and `plot` commands. Do not overwrite old runs.
Stored evidence lives in results/milestone-a; audit documents in docs/onboarding.

The user explicitly decided to retain exact sine torque (2) and leave printed
(4) unchanged. Both energy diagnostics are implemented; the finite-angle
residual of (4) is reported separately. Do not ask the resolved question again.
No neurons, sensor reconstruction, E2E predictor or MPC is implemented.
Milestone B is next only when requested. Windows commands are in README.md;
Windows execution remains unverified. A Linux venv cannot be copied to Windows.

Saving this startup instruction and the installation script to cloud settings
does not itself publish a new cloud snapshot. GitHub publication and cloud
environment publication are separate operations.
