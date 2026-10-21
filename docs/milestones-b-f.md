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

## C: coupled actuation and sparse sensing

The reference integrator splits at every vf_A threshold root and preserves all
eight continuous states. It integrates absolute work (19), signed exact work,
printed (4) work and viscous dissipation as four separate auxiliary states.
The angle limit is terminal; failures are explicit. Root detection excludes
initial/duplicate roots, with opposite crossing directions after each pulse.
No neuronal voltage or mechanical state is reset at current switches.

Detector L is at +.05 degrees, R at -.05 degrees. Pairing consumes only labels
and timestamps: consecutive opposite detectors within .0025s form one pair;
same-detector, nonincreasing-time and timeout cases are recorded/rejected.
No pair is used twice. Crossing timestamp, availability time and signed velocity
are different observation fields. Simulator truth is used only in validation.

Acceptance: exact energy residual <1e-5 of initial energy, reconstructed timing
error <2 microseconds and relative speed error <.002 in the nominal test;
refining integration changes crossing times <.1 microsecond. Four tests passed,
including rejection cases and causal availability. A ten-passage nominal raw
run with detector/switch records is saved in results/milestone-c.

## D: event prediction

Eight-state continuation, one turning point per half swing, signed extrema,
absolute work, angle bounds, transverse-crossing check, detector reach and
finite .1s timeout are explicit. Failed intervals return no amplitude/work.
Three tests passed: consecutive event integrations match uninterrupted
integration within 2e-6 absolute state units / 1e-6 relative; four-event horizon
preserves all states and alternating extrema; timeout, grazing and insufficient
detector excursion remain explicit failures.

Future parameter changes are causal: after a crossing the old candidate's
parameters remain until the outgoing detector; that small tail's work belongs
to the following half-swing. It is included in that interval's objective term.
The predictor accepts an estimated state; it has no plant object or truth-state
access. Saved evidence and reference profiling are in results/milestone-d.
