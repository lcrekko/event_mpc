# Manuscript equation-to-implementation audit

Authority: paper/ECC_2027___Event_Prediction_Scanning_Mirror.pdf, seven pages. The items below are manuscript specifications unless marked as audit finding or implementation proposal. No model is implemented.

| Location | Specification and intended component | Completeness / audit findings |
|---|---|---|
| p2 II-A (1)-(2), Fig.2 | mechanics: alpha'=omega; J omega'=-b omega-k_theta alpha-kappa sin(alpha) I² | Exact nonlinear restoring torque, independent of current sign. Balanced mover; no gravity/electrical transients. SI radians internally. |
| p3 (3)-(4) | validation: E=J omega²/2+k_theta alpha²/2 | **Inconsistent:** (1)-(2) imply E'=-b omega²-kappa sin(alpha) I² omega; printed (4) substitutes alpha. Must clarify before energy validation. |
| p3 II-B | sensing: L at mirror angle +gamma_s, R at -gamma_s; reflected beam angle 2 alpha | Positive traversal R→L. Consecutive opposite detector activations paired within positive Delta_det. Reject same detector/ambiguous order; detailed recovery policy unspecified. |
| p3 (5), p6 (26), Fig.3 | neurons: tau_f vf_i'=-vf_i+gs_minus tanh(vs_i+0.9)-gus_plus tanh(vus_i+0.9)+Isyn_ij+Iext_i; tau_s vs_i'=-vs_i+vf_i; tau_us vus_i'=-vus_i+vf_i. Isyn_ij=gsyn/(1+exp[-2(vs_j+1)]) | Six continuous states; algebraic synapse (no extra synaptic state). Reciprocal inhibition. Numerically stable sigmoid evaluation is an implementation choice. |
| p3 (6), p4 (7)-(9) | actuation: I=I0 indicator(vf_A>=vth); theta=[I0,gs_minus,gus_plus] constant per half-open event interval | Same two gains for both neurons, fixed time constants. Threshold switches must be located, not averaged. |
| p4 (10)-(11), p5 (16)-(19) | predictor: x=[alpha,omega,vf_A,vs_A,vus_A,vf_B,vs_B,vus_B], 8 states. Optional q'=abs(torque*omega), q reset each interval | Start alpha=0, event-derived omega, retained neurons. Return next transverse zero, signed extremum, omega and all neuron states. No resetting neuronal states or velocity. Declared F signature suppresses state dependence and returned continuation states. |
| p4 (12)-(15) | objective: sum j=0..N-1 gamma^j [(t_ref[n+j]-t_hat[j])²+wA(A_ref-A_hat)²+w_tau integral abs(torque*omega)] | As printed, initial timing term is candidate independent; terminal event j=N has no timing penalty. This needs confirmation, not silent reindexing. Absolute mechanical work, not electrical energy or torque squared. |
| p5 (18)-(19), Remarks 2-3 | signed extremum=sgn(omega_start)*max abs(alpha); reject angle-limit violation, missed detector level, no next transverse crossing by Hmax | Assumes one turning point; multiple extrema/grazing tolerances unspecified. Circuit known internally; continuous mechanical state unavailable to MPC. |
| p5 (20)-(22), p6 (23) | optimizer: m=0 mean; M-1 Gaussian perturbations; Euclidean projection onto Theta^N; valid costs weighted exp[-(J-rho)/lambda]; mean is weighted projected candidates | Evaluate mean sequences, retain lowest valid cost across all evaluations; shift sequence and repeat final vector. R indexing/last updated-mean evaluation budget and empty-valid-set handling within a round need clarification. No added smoothing, surrogate or different optimizer. |
| p6 Remark 4 / IV-D | alternatives: uniform random shooting; horizon-constant parameters reduce dimension to 3 | Optional comparisons, not replacements for main projected Gaussian refinement. Final all-invalid fallback I0=0, retain gains; oscillation not guaranteed. |
| p6 (24), p7 V-A.3 | reconstructed timestamp=(t_minus+t_plus)/2; omega_est=2 sigma gamma_s/(t_plus-t_minus) | Only available at t_plus; manuscript explicitly idealizes short sensing and compute delay. Finite-delay causal implementation must retain old parameters until available and propagate full states. No retrospective updates. |
| pp6-7 (25)-(30), Tables I-III | nominal configuration below | Most physical values now supplied; earlier missing-parameter assumptions do not apply. |

## Nominal configuration inventory

Mechanics: J=1e-7 kg m², f0=9.9 Hz, zeta=0.01; k_theta=J(2*pi*f0)², b=2*zeta*J*(2*pi*f0). Table rounded values: 0.3869 mN m/rad, 0.1244 microN m s/rad. Kappa table=30.854 mN m/A², prose rounds to 0.0309 N m/A². Imax=0.12 A, alpha_max=10 deg, gamma_s=0.05 deg, desired signed extrema magnitude 5 deg. Full mirror peak-to-peak range is twice this amplitude; beam deflection is twice mirror angle.

Neurons: gsyn=-1, Iext=-1, gs_minus=2, gus_plus=1.5, vth=0. Dimensionless recurrence PH≈286.320; T=0.05 s (half mechanical period); ct=T/PH≈174.63 microseconds and (tau_f,tau_s,tau_us)=ct*(1,10,100). One nA recurrence per half-swing, two pulses per mechanical period; nominal pulse width ≈13.583 ms. Time constants fixed while gains vary.

Initialization: positive zero crossing alpha=0, omega=5.5137 rad/s; I0≈32.606 mA; neuron A=(-0.7739,-0.4348,-0.4461), B=(-2.3198,-2.4326,-2.1535), ordered fast/slow/ultraslow. Rounded values need not reproduce an exact established periodic orbit.

MPC: N=4 half-swings (nominal 0.2 s), M=256, R=2, gamma=1, gs_minus in [1.8,2.2], gus_plus in [1.3,1.7], sigma_I=0.012 A, other sigmas=.04,.04, diagonal covariance repeated N times. lambda=250 ms²=2.5e-4 s², Hmax=.1 s, rtol=1e-7, scaled atol=1e-9 (scaling not defined), hmax=87.315 microseconds, RNG seed=1. Table K=200 conflicts with prose K=50 (~2.5s). Pair window=.0025 s; Delta_det/Delta_pair appear to denote the same window but require unification.

References: t_ref[j]=jT and A_ref[j,j+1)=(-1)^j*5 deg. wA=T²/(5 deg in radians)²≈.3283 s²/rad²; E0=k_theta*(5 deg in radians)²/2≈1.4733 microJ; w_tau=.05*T²/E0≈84.843 s²/J. Prefer formulas over rounded values after agreement. Free-period regulation is not separately specified; setting individual weights to zero is mentioned.

Numerics: manuscript says adaptive fourth-order Runge–Kutta; SciPy RK45 is embedded 5(4), so exact intended scheme and scaled absolute tolerance remain open. Event exclusion after restart, root tolerances, switching restart, failure status, angle-bound enforcement, dense-output extrema and integration convergence need explicit policies before relevant milestones. These are implementation proposals to document and validate, not additional manuscript equations.

Model knowledge: nominal plant and predictor share parameters, but must be separate instances; noiseless detector timestamps, known controller initialization/state, negligible sensing/optimization delay. Figure 1 specifies sparse event feedback, Fig.2 geometry and beam convention, Fig.3 reciprocal synapses. Results V-B/V-C and conclusions are unfinished; no published simulation evidence is available to reproduce yet.
