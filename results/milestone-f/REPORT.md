# Milestone F simulation results

Generated from saved raw data; no model integration occurs during reporting.
Settings and hypotheses: [experiment plan](../../docs/experiment-plan.md).

| Run | Status / intervals | Timing RMS (ms) | Extrema RMS (deg) | Abs. work (microJ) | Median / p95 optimization (s) | Invalid candidates |
|---|---|---:|---:|---:|---:|---:|
| nominal-seed1 | completed 50/50 | 2.7765 | 0.12293 | 4.6029 | 1.235 / 1.3789 | 0 |
| nominal-seed2 | completed 50/50 | 1.8478 | 0.63508 | 4.2113 | 1.2265 / 1.377 | 0 |
| nominal-seed3 | completed 50/50 | 0.43246 | 0.033063 | 4.6771 | 1.2287 / 1.292 | 0 |
| fixed-nominal | completed 50/50 | 0.00050569 | 0.00013162 | 4.6973 | 0.0061767 / 0.0067556 | 0 |

## Interpretation and limits

These results use literal (13), including its missing terminal timing penalty, and causal sensor availability. Optimization execution time is measured but not injected into simulated actuation delay. Compute-time ratios above one violate a one-interval execution budget on this machine; no real-time claim is supported.
Three-seed summaries report descriptive sample variation, not statistical significance. Mismatch and sensitivity magnitudes are declared evaluation choices; they do not prove robustness beyond these tested cases. Fixed and optimized HCO results must be compared across timing, amplitude and energy together; lower energy alone need not mean better tracking.
All statuses are retained. Metrics for truncated runs describe only their completed prefix and must not be presented as full-horizon success. The final-ten metrics are a descriptive tail window, not a proven steady state. Printed equation (4) is unchanged; exact and printed energy residuals are separate fields.
All candidate costs/statuses, configurations, detector and action histories, raw trajectories, seeds and original source provenance remain in the run directories. Runtime varies by machine and includes optimization work after a separately recorded JIT warmup. Windows execution remains untested.

Unrun configurations: uniform-seed1, uniform-seed2, uniform-seed3, constant-seed1, long-200, mismatch-kappa, mismatch-damping, budget-64, horizon-2.

## Figures

![Comparison](figures/comparison.png)

![All runs](figures/all-runs.png)

![Parameters](figures/nominal-parameters.png)

![Long run](figures/long-run.png)

![Neurons](figures/neurons.png)
