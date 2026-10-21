**Project purpose**

Develop reproducible Python simulations for an academic paper on event-centric model predictive control of a scanning mirror with a neuromorphic controller.

**Scientific authority**

- Use the latest manuscript in `paper/` as the primary specification, together with my subsequent clarifications.

- Associate implemented dynamics, objectives, constraints, and algorithms with their equation numbers or manuscript pages.

- Record missing information and inconsistencies explicitly. Do not silently invent physical parameters, initial conditions, controller rules, or experimental settings.

- Distinguish manuscript specifications, my decisions, and implementation choices in the documentation.

- Keep demonstration configurations clearly separate from configurations used for paper results.

**Development environment**

- Target Windows, Python, and VS Code.

- Provide PowerShell-compatible commands and use a project-local `.venv`.

- Inspect the existing Python environment before selecting dependencies.

- Use portable paths through `pathlib` and keep the initial implementation suitable for a CPU.

- Keep the numerical implementation in reusable Python modules. Notebooks may support exploration.

- Add dependencies only when they serve a clear purpose.

**Working method**

- Complete one bounded milestone at a time.

- Make routine implementation decisions independently and explain material choices.

- Ask concise, grouped questions when unresolved scientific choices block progress. Continue independent work where possible.

- Preserve existing work and inspect Git changes before modifying files.

- Run meaningful checks appropriate to each milestone. Report what actually ran, what passed, and what remains unverified.

- Preserve continuous model states when parameters change unless the manuscript explicitly specifies a reset.

**Reproducibility and communication**

- Save raw numerical results together with configurations, seeds, numerical tolerances, software versions, and code-version information.

- Keep simulation, metric calculation, and plotting separate so figures can be regenerated without rerunning simulations.

- Explain changes in plain language, linking them to the mathematical model.

- At each milestone, provide the exact run command, the resulting evidence, unresolved issues, and the next recommended task.
