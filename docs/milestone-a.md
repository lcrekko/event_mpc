# Milestone A: mechanical model

## Scope and scientific decisions

The primary source is `paper/ECC_2027___Event_Prediction_Scanning_Mirror.pdf`.
Only mechanical dynamics and prescribed currents are implemented. No neuron,
sensor reconstruction, event-to-event predictor, optimizer or MPC is implemented.
The example is a demonstration, not evidence for the paper's closed-loop results.

User decision: retain the exact sine torque in (2), keep printed (4) unchanged,
and proceed according to the paper. Accordingly, the simulator integrates

```
alpha' = omega
J omega' = -b omega - k_theta alpha - kappa sin(alpha) I²   (1), (2)
E = J omega²/2 + k_theta alpha²/2                         (3)
```

Printed (4), `-b omega² - kappa I² alpha omega`, is available unchanged through
`paper_energy_rate` and its signed-work integral. It is reported as a diagnostic.
The chain rule applied to the actual simulated equations gives
`E' = -b omega² - kappa I² sin(alpha) omega`. These are different for finite
angles. The validation cannot truthfully assert both as exact identities.
The model, manuscript and printed (4) are not altered to remove this discrepancy.

The exact diagnostic residual is `E(t)-E(0)-W_exact(t)+D(t)`; the printed (4)
diagnostic is `E(t)-E(0)-W_4(t)+D(t)`. Here D is the integral of `b omega²`,
W_exact the integral of exact torque times omega, and W_4 the integral of
`-kappa I² alpha omega`. Signed work is distinct from the absolute-work MPC
objective (13) and electrical energy. These auxiliary integrals do not drive
the mechanical trajectory. Their initial values are zero; they are never reset
at a prescribed current switch.

## Units and configuration provenance

All internal quantities are SI: mirror angle in radians, angular velocity in
rad/s, current in A, torque in N m and energy in J. Figures convert mirror
angle to degrees; beam deflection would be twice the mirror angle. No beam
signal is simulated.

Table I and (25): J=1e-7 kg m², f0=9.9 Hz, zeta=.01;
stiffness and damping are computed from (25), rather than rounded table entries.
Use table kappa=.030854 N m/A², Imax=.12 A, alpha_max=10 degrees.
Using the tabulated kappa and formula-derived stiffness/damping is an explicitly
recorded precision choice. Initial alpha=0 and omega=5.5137 rad/s come from
V-A.3. Current .032606 A comes from the manuscript; the manually prescribed
switching schedule in `configs/mechanical_demo.json` is an implementation
demonstration choice and does not claim to reproduce HCO pulse timing.

## Numerical method and failure handling

SciPy `solve_ivp`, RK45 (embedded 5(4), an implementation choice for this
milestone). This is not a claim to implement the unspecified adaptive fourth-order
algorithm in V-A.4 exactly. Default rtol=1e-9; absolute tolerances for
`[alpha, omega, W_exact, W_4, D]` are `[1e-11,1e-9,1e-16,1e-16,1e-16]`
in the corresponding SI units. This explicit vector avoids guessing what the
paper means by its scaled absolute tolerance. Maximum step=87.315 microseconds,
the paper's Table III value. Refined check: rtol=1e-11, atol reduced by 100,
max step halved. Settings and parameters are immutable dataclasses that callers
can supply independently to separate plant/predictor instances later.

Each known current discontinuity splits the integration; all five state
components continue at the boundary. Inputs are right-continuous and endpoints
are stored only once. Root functions are alpha (zero crossing), omega (turning
point), and alpha_max-abs(alpha) (terminal angle limit). Initial and duplicate
crossings are excluded with 1e-12 s initial and 1e-10 s duplicate windows;
zero crossings also require abs(omega)>1e-10 rad/s. Turning points must have
nonzero acceleration, to exclude a stationary equilibrium. These thresholds
are explicit numerical choices, not manuscript values or detector logic.
Root detection requires isolated roots; this is not a grazing-event detector.

Every schedule has a finite final time and nonnegative, finite currents bounded
by Imax. Invalid configuration raises ValueError; solver failure and angle-limit
termination return explicit `integration_failed` / `angle_limit` status and the
available partial trajectory. The CLI returns nonzero for both. No trajectory
is clipped and no failed rollout is reported as successful. This is a mechanical
simulation API, not yet the event-prediction timeout interface of Milestone D.

## Acceptance criteria declared before validation

These deterministic checks are reliability checks, not statistical experiments.
For the unforced response over .3 s (about three periods): analytical angle
error <=1e-8 rad, speed error <=1e-6 rad/s, crossing error <=1e-8 s, exactly
five noninitial crossings, and no energy increase above 1e-14 J between stored
nodes. Angle and speed thresholds are roughly 1e-7 of nominal scales; root
threshold is 2e-7 of a 50 ms interval. These are substantially below the physical
sensor separation and amplitude scales.

For a switched-current case (.12 A/0 A, with switches at .025,.05,.075 s,
ending .15 s), exact integrated energy residual <=1e-7 of initial energy.
This is about 1.5e-13 J, tight enough to catch sign or unit errors. Printed
(4)'s nonzero residual is reported separately, without a false pass criterion;
its rate difference from the chain rule is checked algebraically to 1e-18 W.

Refining tolerances and maximum step must preserve crossing and turning counts,
change event times by <=1e-7 s, extrema by <=1e-7 rad, final state by <=1e-7
when scaled by [.1 rad,10 rad/s], and signed work by <=1e-12 J. This absolute
work bound is below 1e-6 of the initial energy. Counts/status cannot be replaced
by a zero-event run. Restoring torque, current-sign invariance, the exact sine
formula, state continuity at switches, stationary equilibrium, input rejection
and physical-limit termination receive separate unit checks.

## Outputs and next milestone

Each run directory contains raw adaptive-node trajectories, event times,
turning angles, actual current, configuration, parameters, solver settings,
software versions, Git HEAD/status and source SHA256 hashes. No random numbers
are used (seed recorded as null). Dirty/uncommitted sources are identified;
these runs do not imply a published or committed code revision. Metrics and
plots are generated from saved data, without rerunning integration.

See the README for commands and `docs/milestone-a-results.md` for actual evidence.
The next bounded task is Milestone B: independent neurons and reciprocal
synapses, then rhythm/threshold/time-scale checks. No new scientific answer is
needed for the mechanical implementation. The documented (4) discrepancy remains;
the paper's exact RK method and scaled absolute tolerance need clarification
before claiming identical reproduction of its numerical method.
