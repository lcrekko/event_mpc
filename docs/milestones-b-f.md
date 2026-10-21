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

## E: MPC, optimizer, and computational implementation

Implemented (13) literally: gamma^j weights each full bracket, j=0..N-1.
The first timing term is constant across candidates and the terminal event has
no timing penalty. No reindexing or alternative objective has been introduced.
Absolute torque-times-speed integral is not electrical energy.

Implemented projected Gaussian samples with diagonal covariance, M candidates
including mean, normalized exp[-(J-rho)/lambda] weights, and R=2 updates. Each
updated mean is evaluated, including the final one; all valid candidates/means
compete for the returned best sequence. Thus M=256,R=2 costs 514 evaluations.
This explicit indexing convention resolves the draft's ambiguous round numbering.
Initial mean repeats nominal theta. Shift/repeat-last (23) initializes the next
event. If a round is all-invalid retain its mean and continue the remaining
rounds; if every evaluation is invalid set current=0 and retain previous gains.
This intermediate-round policy is an implementation choice. No smoothing,
surrogate, warm-start modification or optimality guarantee is claimed.

The controller reconstructs the mechanical zero state using (24) and propagates
it and its owned circuit state with old parameters until information availability.
It never reads the plant's angle, velocity, true crossing time, or predictor's
true initialization after the initial known state. Reconstructed-time to
availability work is included as a candidate-independent first-interval term.
Future candidate switches are similarly delayed to the outgoing detector.
Optimizer execution time is measured but **not injected as simulated delay**.
This implements causal sensor delay while still idealizing computational delay.

Profiling of the reference four-event predictor gave about .445s per candidate,
making full CPU experiments impractical without acceleration. Added Numba solely
for compiled numerical evaluation. NumPy remains 2.3.5. The accelerated solver
uses classical RK4 with two-half-step error estimation (difference/15), explicit
component scales matching the reference, maximum step 87.315 microseconds,
rtol=1e-7, and bracketed pulse/turning/crossing/limit roots to <=1e-12s. Each
located discontinuity restarts the integrator without resetting physical states.
It is a separate adaptive fourth-order implementation, not SciPy RK45 and not
a claim of bitwise reproduction of the draft's unspecified solver. No fast-math.
Four CPU threads parallelize independent candidates, with deterministic RNG
sampling done before parallel evaluation. Compilation warmup is reported apart.

Acceptance before use: compare five four-interval sequences, including uniform
wide-bound draws, against independent SciPy reference. Event differences <=.2
microseconds, extrema <=2e-6 rad, work <=2e-10 J plus 1e-4 relative, continuation
state <=2e-4 absolute plus 1e-4 relative, cost <=2e-8 s². Repeat with half step and
rtol=1e-9; validate failure status. These thresholds are below sensor separation
and amplitude scales, and do not stand in for closed-loop robustness evidence.

All 26 tests passed, including the backend, optimizer algebra, literal objective,
fallback, best-candidate retention, mean evaluation, constant/uniform alternatives,
state continuation, and a small sensor-only causal closed loop. A three-interval,
M=8 debug run completed and is saved in results/milestone-e/debug. It is explicitly
a debugging example, not the planned paper-scale experiment. Reproduce:

```
python -m event_mpc.closed_loop --output outputs/debug --intervals 3 --samples 8
python -m event_mpc.profile --output outputs/predictor-profile.json
```

Set NUMBA_NUM_THREADS=4 for the recorded cloud resource budget (4 CPU quota,
32GiB memory). Windows PowerShell: `$env:NUMBA_NUM_THREADS="4"` before running.
