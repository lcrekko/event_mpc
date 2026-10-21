**Objective and working context**

Help me build a reliable simulation project for my paper on event-centric MPC. I use Windows, Python, and VS Code. I understand the control theory, but I am new to working with Codex. Explain important software decisions clearly and keep the project understandable.

The manuscript is:

`paper/ECC_2027___Event_Prediction_Scanning_Mirror.pdf`

The scientific sections are drafted; simulation results remain to be developed. Your task is to implement the formulation faithfully and produce reproducible numerical evidence.

Begin with the initial assignment at the end of this document. The subsequent milestones describe the intended development sequence; they are not instructions to implement everything immediately.

**1. Read and audit the manuscript**

Read the complete manuscript, including algorithms, figures, captions, and assumptions.

If equations cannot be extracted reliably from the PDF, identify the affected equations and request the relevant LaTeX source or clarification. Do not guess symbols, subscripts, signs, or matrix dimensions.

Prepare a specification audit covering:

- Mechanical dynamics, torque law, physical parameters, units, and operating limits.

- Neuron dynamics, synaptic coupling, state ordering, and relevant time scales.

- Current-generation rules, thresholds, and switching behavior.

- Sensor locations, detector events, zero-crossing reconstruction, and velocity estimation.

- Tunable parameters, admissible sets, initialization, and parameter-update rules.

- Event-to-event prediction model, prediction horizon, objective, and constraints.

- Each numerical optimization algorithm actually proposed in the manuscript.

- Assumptions concerning model knowledge, measurement availability, and computational delay.

For each item, identify its manuscript location, whether it is fully specified, and any information required for implementation.

Pay particular attention to conventions that can cause numerical discrepancies: radians versus degrees, mirror angle versus beam deflection, amplitude versus scanning range, signed versus absolute quantities, and event-to-event duration versus a complete oscillation period.

**2. Verify the project background**

Our previous formulation involved a scanning mirror, a half-center oscillator, sparse photodetector feedback, and online tuning of current and neuron parameters.

Treat this description as orientation. Verify every detail against the current manuscript.

In particular, establish:

- The complete state required to continue a prediction, including any neuron or synaptic states.

- Which states and measurements are available to the MPC.

- How the next event is detected and how interval outputs are calculated.

- Which parameters remain constant between successive events.

- Whether the draft includes prescribed-period tracking, free-period operation, or both.

Do not silently substitute a simpler controller, continuous state feedback, or a different optimization algorithm.

**3. Preserve the information structure and causality**

Separate the simulated plant’s full state from the information supplied to the controller.

The simulator may use full state information for integration and validation. The controller must receive only the measurements, event history, actuation history, and known internal states permitted by the manuscript.

For photodetector-based zero-crossing reconstruction, distinguish:

- The physical crossing time.

- Its reconstructed timestamp.

- The time when sufficient sensor information becomes available.

- The time when updated parameters are applied.

If the manuscript idealizes these times as identical, document that assumption. If the distinction creates an implementation ambiguity, flag it before selecting a different control law.

Do not apply a parameter update retrospectively using information obtained later.

**4. Use a modular numerical architecture**

Propose a small structure that separates:

- Mechanical and neuron dynamics.

- Actuation and event detection.

- Event-to-event prediction.

- Objective and constraint evaluation.

- Parameter-sequence optimization.

- Closed-loop execution.

- Experiment configurations, metrics, and figures.

Create modules as they become useful. Avoid a large collection of empty files or unnecessary abstractions.

Keep plant and predictor instances separate, even when they initially share identical equations and parameters. This should allow later mismatch experiments without changing the controller’s information interface.

**5. Establish numerical reliability before optimization**

Use an ODE solver with event detection, such as SciPy’s `solve_ivp`, unless a different approach is justified.

Document the integration method, relative and absolute tolerances, maximum step size, event functions, and treatment of switching.

The implementation must address:

- Spikes and current switches occurring on faster time scales than the mechanical motion.

- Duplicate event detection after restarting at a crossing.

- Missing or incorrectly ordered detector events.

- Grazing crossings or ambiguous detector pairs.

- Rollouts that fail to produce the required next event.

- Physical-limit violations and integration failures.

- Accurate interval extrema and objective integrals.

Use explicit rollout status values and finite timeouts. Do not represent a failed rollout as a successful prediction with fabricated outputs.

Validate the simulator using independent checks where possible. These should include an analytical mechanical response in an appropriate special case, the mechanical energy balance derived from the verified dynamics, and convergence of event times and interval outputs as numerical settings are refined.

Numerical acceptance thresholds should be stated and justified before assessing the corresponding results.

**6. Implement in successive milestones**

Milestone A — Mechanical model

Implement the mirror with prescribed current. Validate the unforced response, torque convention, and energy balance.

Milestone B — Neuromorphic controller

Implement the neurons and synapses independently. Check their dynamics and expected rhythmic behavior before coupling them to the mirror.

Milestone C — Coupled system and sensing

Connect the controller, current-generation mechanism, and mirror. Add detector events and the sensing reconstruction specified in the paper. Compare reconstructed quantities against simulator truth for validation.

Milestone D — Event-to-event predictor

Implement a rollout from the current event to the next admissible event. Return the outputs and continuation state required by the formulation, together with validity information.

Check that consecutive event rollouts agree with a continuous simulation under the same parameter schedule.

Milestone E — EC-MPC

Implement the stated objective, constraints, candidate-generation procedure, and receding-horizon loop.

Verify that the horizon counts the intended events, the first parameter vector is applied over the intended interval, and all continuation states are preserved.

Milestone F — Paper experiments

Develop the nominal experiments first. Then add agreed comparisons, sensitivity studies, mismatch cases, and computational-cost measurements.

Each milestone must have a runnable example, appropriate validation, and a short explanation before proceeding.

**7. Reproduce the proposed optimizer faithfully**

Extract the optimizer’s sampling distribution, bounds handling, initialization, update rule, weighting or temperature parameters, termination criterion, and candidate-selection rule from the manuscript.

Clearly distinguish the algorithm in the paper from any additional engineering modifications.

For example, do not silently introduce clipping, smoothing, warm starts, different sampling distributions, or surrogate models.

If the algorithm evaluates updated means or retains the best valid candidate across iterations, reproduce that behavior exactly.

Identify what happens when every evaluated candidate is invalid. If no fallback is specified, record this as an unresolved design question.

Initially use a small computational budget for debugging. Profile the validated implementation before introducing performance optimizations.

**8. Prepare experiments that support identifiable claims**

Before running a large experiment, specify the question it addresses, the comparison, the metric, and the relevant configuration.

Potential quantities include:

- Zero-crossing timing errors.

- Scanning-range tracking.

- Transient and steady oscillatory behavior.

- Actuation effort and mechanical energy exchange.

- Parameter evolution.

- Invalid-rollout and optimization-failure rates.

- Computation time relative to event intervals.

Use the definitions in the paper. Keep mechanical work, torque-squared effort, and electrical energy distinct.

For comparisons, use consistent initial conditions, reference signals, numerical accuracy, and clearly stated computational budgets.

For randomized optimization, save seeds and assess variability across repeated runs. Preserve failures in the results and report how they are handled.

Report whether computation delay is included in the simulated control loop. Measured execution time alone should not be presented as a real-time guarantee.

**9. Save reproducible outputs**

Each experiment should save:

- The complete configuration and initial conditions.

- Raw trajectories and event records.

- Applied parameter sequences and optimization diagnostics.

- Numerical settings, random seeds, software versions, and code-version information.

- Calculated metrics and failure statuses.

Save each run separately. Provide commands to regenerate figures from saved data.

Default plots should work without requiring a separate LaTeX installation. Publication formatting can be added after the numerical results are validated.

**Initial assignment — complete this first**

Complete only the manuscript audit and development-environment setup.

1. Inspect the project and existing files without overwriting my work.

2. Read the manuscript and prepare an equation-to-implementation map.

3. List missing parameters and scientific ambiguities. Separate blocking questions from choices that can be deferred.

4. Inspect the available Python installation and propose a minimal compatible dependency set.

5. Create or reuse a project-local `.venv`, record dependencies, and verify the environment with actual import checks.

6. Provide Windows PowerShell commands and explain how to select this interpreter in VS Code.

7. Create a concise README, specification audit, open-question list, and milestone plan.

8. Summarize readiness for Milestone A and ask only the questions necessary to begin it.

Do not implement the full simulation or run parameter searches during this initial assignment.

If scientific information is missing, finish the independent setup and documentation work first. Leave dependent numerical work explicitly pending.

Your final response should explain what you inspected, what you created, what you actually verified, and what information I need to supply next.
