# Milestone A verification evidence

The originally cloud-only evidence described below has also been copied into
`results/milestone-a/` for GitHub publication: `validation.json` and the `demo/`
directory. The historical `outputs/` paths remain the original run locations.
The implementation and documents are now included in the direct Solid_first
commit; the original metadata correctly retains the pre-commit run state.

Executed in the prepared Linux cloud environment with Python 3.12.14,
NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8. Windows commands are
documented but Windows execution remains unverified.

## Completed checks

`python -m unittest discover -s tests -v`: **8 tests passed**.
`python -m event_mpc validate`: **13 numerical checks passed**.
The thresholds were documented in milestone-a.md before execution.

| Check | Measured | Acceptance threshold |
|---|---:|---:|
| Unforced analytical angle error | 1.47e-15 rad | 1e-8 rad |
| Unforced analytical speed error | 1.01e-13 rad/s | 1e-6 rad/s |
| Unforced zero-crossing time error | 1.39e-16 s | 1e-8 s |
| Unforced energy increases | 0 J | 1e-14 J |
| Forced exact energy relative residual | 7.76e-14 | 1e-7 |
| Refined crossing-time difference | 2.78e-16 s | 1e-7 s |
| Refined extremum difference | 4.30e-15 rad | 1e-7 rad |
| Refined final-state scaled difference | 4.30e-14 | 1e-7 |
| Refined signed-work difference | 4.60e-20 J | 1e-12 J |

The unforced run produced all five expected noninitial crossings. Torque
direction, squared-current convention, switching continuity, input rejection,
stationary-state handling and terminal angle-limit status also passed.
The machine-readable report is `outputs/milestone-a-validation.json`.
Very small errors here reflect the conservative maximum step for this smooth
mechanical problem; they do not establish accuracy of a future spiking system.

For the forced validation case, the unchanged printed equation (4) gives a
maximum integrated residual of **2.3732e-10 J**, or **0.01561%** of initial
energy. This is a documented finite-angle discrepancy, not an integration
failure and not a claim that (4) is an exact identity for equation (2).

## Prescribed-current demonstration

Actual commands executed from the repository root:

```bash
.venv/bin/python -m event_mpc run --output outputs/milestone-a-demo
.venv/bin/python -m event_mpc metrics outputs/milestone-a-demo
.venv/bin/python -m event_mpc plot outputs/milestone-a-demo
```

Run status **completed**, duration .3 s, 3444 stored adaptive samples,
6 noninitial zero crossings and 6 turning points. Maximum sampled mirror
angle magnitude 4.93247 degrees, inside the 10-degree limit. Exact energy
relative residual 5.15e-14. Printed (4) diagnostic residual 2.0362e-10 J
(0.01340% of initial energy).

The run directory contains trajectory.npz, metadata.json, status.json,
metrics.json and mechanical.png. Raw data, current schedule, events and source
hashes are preserved. Plot regeneration was exercised from saved data and the
generated image inspected. Outputs and the venv are Git-ignored; source and
documentation are newly created, uncommitted files. Existing tracked documents
and the manuscript remain unchanged. This is a prescribed-current demonstration,
not an HCO or MPC paper result.

Milestone A is complete. Milestone B (neurons and reciprocal synapses) is the
recommended next bounded task. The exact adaptive RK scheme and scaled absolute
tolerance intended in the manuscript remain open for later method matching;
this milestone's explicit RK45 settings are fully recorded.
