"""Run, inspect, plot and validate Milestone A from the repository root."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import scipy
from .mechanics import MechanicalParameters, SolverSettings, simulate
from .metrics import mechanical_metrics

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def provenance(seed=None, randomness="none; deterministic integration"):
    def git(*args):
        p = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True)
        return p.stdout.strip() if p.returncode == 0 else "unavailable"
    return {"head": git("rev-parse", "HEAD"), "git_status": git("status", "--porcelain"),
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((ROOT/"event_mpc").glob("*.py"))},
            "python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__,
            "platform": platform.platform(), "seed": seed,
            "randomness": randomness}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--config", type=Path, default=ROOT/"configs"/"mechanical_demo.json")
    run.add_argument("--output", type=Path)
    for command in ("metrics", "plot"):
        sub = commands.add_parser(command)
        sub.add_argument("run_dir", type=Path)
    val = commands.add_parser("validate")
    val.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        config = json.loads(args.config.read_text(encoding="utf-8"))
        p, settings = MechanicalParameters(), SolverSettings()
        output = args.output or ROOT/"outputs"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        output.mkdir(parents=True, exist_ok=False)
        write_json(output/"metadata.json", {"config": config, "parameters": asdict(p),
                   "derived": {"stiffness": p.stiffness, "damping": p.damping},
                   "solver": {"method": "RK45", **asdict(settings)}, "provenance": provenance(),
                   "state_columns": ["alpha_rad", "omega_rad_s", "signed_exact_work_J",
                                     "signed_equation_4_work_J", "dissipation_J"]})
        result = simulate(config["initial_state"], config["segments"], p, settings)
        np.savez_compressed(output/"trajectory.npz", time=result.time, state=result.state,
                            current=result.current, zero_times=result.zero_times,
                            turning_times=result.turning_times, turning_angles=result.turning_angles)
        write_json(output/"status.json", {"status": result.status, "message": result.message,
                                          "nfev": result.nfev})
        print(output)
        return 0 if result.status == "completed" else 1
    if args.command == "validate":
        from .validation import validate
        report = {**validate(), "provenance": provenance()}
        if args.output:
            # Refuse to overwrite an earlier validation record.
            with args.output.open("x", encoding="utf-8") as f:
                json.dump(report, f, indent=2, allow_nan=False)
        print(json.dumps(report, indent=2))
        return 0 if report["passed"] else 1
    meta = json.loads((args.run_dir/"metadata.json").read_text(encoding="utf-8"))
    p = MechanicalParameters(**meta["parameters"])
    with np.load(args.run_dir/"trajectory.npz") as data:
        if args.command == "metrics":
            m = mechanical_metrics(data["state"], p)
            write_json(args.run_dir/"metrics.json", m)
            print(json.dumps(m, indent=2))
        else:
            # Use a writable repository cache without requiring shell activation.
            import os
            os.environ.setdefault("MPLCONFIGDIR", str(ROOT/".mplconfig"))
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from .mechanics import energy
            t, y = data["time"], data["state"]
            fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 7))
            axes[0].plot(t, np.rad2deg(y[0])); axes[0].set_ylabel("Mirror angle [deg]")
            axes[1].step(t, data["current"]*1000, where="post"); axes[1].set_ylabel("Current [mA]")
            change = energy(*y[:2], p)-energy(y[0,0],y[1,0],p)
            axes[2].plot(t, (change-y[2]+y[4])*1e9, label="Exact balance")
            axes[2].plot(t, (change-y[3]+y[4])*1e9, label="Eq. (4) diagnostic")
            axes[2].set_ylabel("Residual [nJ]"); axes[2].set_xlabel("Time [s]"); axes[2].legend()
            fig.suptitle("Milestone A: prescribed-current demonstration")
            fig.tight_layout(); fig.savefig(args.run_dir/"mechanical.png", dpi=160); plt.close(fig)
            print(args.run_dir/"mechanical.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
