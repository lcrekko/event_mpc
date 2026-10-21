# Completed work and publication record

## Environment and initial inspection

- Waited for the cloud environment to become ready; inspected the existing
  checkout and GitHub read access. Initially the repository had no commits.
- After the user populated the repository, fetched `Solid_first` at
  f732082dbc1a7ca5149ed37290d8e3d1f5420462 and checked it out. Read AGENTS.md,
  CODEX_SETUP.md and the seven-page manuscript, including figures and tables.
- Created the project-local Python 3.12 venv, installed NumPy/SciPy/Matplotlib
  and recorded full dependency versions. Corrected the cloud cache location to
  a writable path; integrity checks were not disabled.
- Verified imports, an analytical scalar ODE solution, event detection,
  dependency compatibility and headless plotting. Windows execution was not
  available and is not claimed.
- Produced the audit, questions, milestone plan and Windows instructions.
  These were originally outside the checkout; copies are now in docs/onboarding.
  Their original historical wording is retained. Later decisions are appended.

## Milestone A

- User directed exact equation (2), unchanged equation (4), and mechanical
  model implementation. Added reusable mechanics, prescribed-current integration,
  explicit status handling, numerical validation, tests and separate data/metric/
  figure commands. Manuscript and CODEX_SETUP.md remain unchanged.
- Executed 8 passing tests and 13 passing numerical checks, then the prescribed
  current demonstration. Exact energy balance closes numerically; printed (4)'s
  finite-angle residual is explicitly reported. No neurons or MPC implemented.
- Saved trajectories, current schedule, events, status, metrics, figures,
  software versions and original source provenance. Selected evidence is now
  versioned in results/milestone-a, with the original metadata intact. New runs
  go under ignored outputs/.
- Saved installation and startup instructions to the cloud configuration draft.
  Their repository copies are scripts/install-cloud.sh and docs/cloud-start.md.
  No cloud publication was performed by the agent.

## GitHub workflow requested by the user

All completed source, documentation, selected outputs and reusable environment
instructions are being committed and pushed directly to Solid_first. AGENTS.md
records the standing instruction to commit/push after each completed change.
Venvs, caches and temporary PDF rendering/text files stay out of Git; the paper
and reproducible setup instructions are retained instead. Cloud authentication,
private configuration IDs and credentials are not exported.

The original run metadata records an uncommitted code state, because these runs
preceded the first implementation commit. Its source hashes document the actual
code used. Do not substitute a later Git commit into those historical records.

## Subsequent Milestones B–F

- User authorized completing B–F and explicitly approved literal objective
  indices, causal sensor availability and both K=50 and K=200 experiment lengths.
- B implemented and independently verified six-state reciprocal neurons. C
  coupled exact mechanical dynamics and threshold-switched current with detector
  reconstruction. D validated complete state continuation across events and
  explicit invalid-rollout statuses. Each milestone was committed and pushed.
- E implemented projected Gaussian refinement and uniform/constant alternatives,
  objective, causal sensor-only state reconstruction and receding-horizon updates.
  A compiled adaptive fourth-order numerical backend was introduced only after
  profiling and checked against independent SciPy integration and refinement.
  NumPy stayed at the established pin; Numba/llvmlite are additional recorded
  dependencies. All candidate sequences, costs and failure codes are preserved.
- F's declared plan, runtime evidence, solver audits and each completed group of
  raw results are committed and pushed as the suite runs. The report explicitly
  lists unrun configurations until the suite finishes. No solver outcome is
  replaced with fabricated data, and poor tracking results remain in the report.
- Chinese local-development guidance and full cloud setup/startup instructions
  now live in the repository. Saved cloud configuration and GitHub pushes are
  separate from publishing a cloud environment snapshot.
