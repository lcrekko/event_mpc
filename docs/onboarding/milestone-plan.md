# Bounded milestones

Current initial milestone: repository inspection, seven-page audit, local venv, minimal pinned numerical stack, environment smoke tests and Windows instructions. Completed; model validation remains unrun.

A. Implement reusable mechanics and prescribed-current example only after energy clarification. Validate analytical unforced damped response, exact torque convention, and integrated energy balance. State tolerances and acceptance criteria before running. Save configuration, solver settings, code version and raw results.
B. Separate neurons/synapse module; verify rhythm, threshold events and fast time-scale convergence before coupling.
C. Couple actuation and sensing; distinguish true event, reconstructed timestamp, information availability and application time. Validate sensor estimates against truth without exposing truth to controller.
D. Implement predictor with explicit continuation state, extrema/work outputs and failure statuses. Verify consecutive event rollouts against continuous simulation. Resolve integration choices here.
E. Implement exact manuscript sampling/refinement, constraints and receding horizon with small debug budget. Preserve states, evaluate means, retain best candidate and test fallback. Resolve objective indexing first.
F. Agree experiments, comparisons and metrics; then measure performance and runtime. Store seeds and failures; separate simulation, metric processing and figure regeneration. Runtime measurements alone are not a real-time guarantee.

Proposed architecture as modules become needed: mechanics, neurons, actuation/sensing, prediction, objective/constraints, optimization, closed_loop; separate experiment configurations and postprocessing. No empty module scaffolding or full controller implementation in onboarding.

Update: Milestone A completed following the user's instruction to retain equations (2) and (4). Eight unit tests and thirteen numerical checks passed. See repository docs/milestone-a-results.md for evidence and commands. Next bounded task is Milestone B; it has not been started.

Subsequent update: the user authorized all B–F work. B–E implementation and
validation are complete; F's 13 declared experiments completed 800 total
intervals. See ../milestones-b-f.md and ../../results/milestone-f/REPORT.md.
The historical “B not started” statement above describes the earlier checkpoint.
Current results require improved tracking evidence and computation speed before
claiming paper-level control advantages or real-time deployment.
