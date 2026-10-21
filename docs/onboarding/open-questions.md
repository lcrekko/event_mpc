# Open questions

## Required before Milestone A energy validation

Should mechanical simulations retain the exact sine torque (2), with energy balance E'=-b*omega²-kappa*sin(alpha)*I²*omega, treating (4) as a small-angle approximation? This is the only scientific clarification required to begin Milestone A. Physical parameters and a nominal initial condition are supplied in the current manuscript. Proposed numerical convention for approval with this question: use SI units, derive k_theta and b via (25), and use table kappa=.030854 N m/A² rather than prose rounding.

## Can be deferred until affected milestones

- B: use ct=T/PH or rounded table time constants? Precision of established-orbit initial neuronal states; no need to reconstruct a different orbit silently.
- C/D: implement idealized event-time feedback or causal finite-delay application? Confirm pairing-window naming, recovery from unpaired detections and grazing/multiple-turning-point behavior.
- D: which adaptive RK method and scaled-atol definition? Define numerical root/exclusion tolerances and convergence acceptance thresholds before assessing results.
- E: keep (13) timing indices 0..N-1, omitting terminal event penalty? Define initial nominal sequence, exact round indexing and final-mean evaluation count, intermediate all-invalid-round behavior. Final all-invalid fallback is already specified.
- F: K=200 in table or K=50 in prose? Which comparisons and claims first? Free-period experiment not presently defined.

These questions do not prevent installing or testing the development tools. No parameter searches or manuscript simulations have been run.

## Subsequent user decision and Milestone A completion

The user explicitly requested retaining exact (2), leaving (4) unchanged, and beginning Milestone A. This resolves the approval-to-proceed question above. Both diagnostics are retained; no paper equation was edited. Milestone A is now implemented and verified in the repository. See /workspace/event_mpc/docs/milestone-a.md and docs/milestone-a-results.md. No further answer is needed for Milestone A; later milestone questions remain deferred.

## Subsequent B–F decisions

The user authorized all B–F work and approved: literal j=0..N-1 timing indices;
causal parameter application after the second detector event; K=50 main runs
and an additional K=200 run. Formula (27) time constants are used unchanged;
rounded initial states remain as supplied. RK45 reference and a validated
adaptive fourth-order compiled backend use explicit recorded component scales.
Initial optimizer mean repeats nominal theta; each updated mean is evaluated;
an empty round retains its mean, and final total failure uses the manuscript's
zero-current/retained-gain fallback. These choices are documented in
../milestones-b-f.md. Optimizer wall time is measured but excluded from simulated
delay. A free-period formulation remains unspecified and is not invented.
These supersede the historical deferred items above for the implemented scope.
