# Milestones B–F: execution record and explicit choices

These extend the completed mechanical milestone. The manuscript remains the
scientific authority; equation (2) is exact and printed equation (4) unchanged.
Results distinguish manuscript specifications from implementation choices.

## B: neurons

Implemented equations (5), (26) directly with six continuous voltages ordered
fast/slow/ultraslow for A then B. Synapses are algebraic (no hidden states).
Use formula (27), ct=.05/286.320 seconds, not rounded time constants. The
rounded initialization (29) is used unchanged; gains default to (2,1.5).
Stable logistic evaluation avoids overflow without changing the formula.
Acceptance before running: scalar formula agreement, exchange symmetry,
at least five A upcrossings in .3s, last three recurrence periods within .2ms
of .05s, and event changes <=.1 microsecond on step/tolerance refinement.

Run: `python -m unittest discover -s tests -p test_neurons.py -v`.
Verified: three neuron tests passed. In the .5s saved run, last five recurrence
periods were .05000004s; maximum refined event change was 2.59e-12s.
Raw voltages, threshold events, parameters and provenance are in
`results/milestone-b/`. These validate the circuit independently of mechanics.

All `python` commands use the project-local venv; Windows interpreter is
`.venv\Scripts\python.exe` and Linux `.venv/bin/python`.

## Remaining scientific decisions

User approved: retain literal objective timing indices j=0..N-1; apply new
parameters only after the second detector event, with causal state propagation;
primary K=50 intervals plus a K=200 run for the table alternative. Use original
rounded initialization without recalibration. B is independent of these decisions.
Exact RK45 numerical implementation remains an explicit choice, not a claim
of matching the draft's unspecified adaptive fourth-order algorithm.
