"""Runner for the Cantera C01 constant-pressure ignition capability."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .postprocess import summarize_profile, write_profile_csv
from .report import write_validation_report
from .validation import validate_metrics


def _import_solver_stack() -> tuple[Any, Any]:
    try:
        import cantera as ct
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Cantera is required to execute this capability. Install cantera>=3.2 "
            "in the active environment, then rerun the C01 case."
        ) from exc

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, plt


def _tracked_species(config: dict[str, Any]) -> list[str]:
    return list(config["outputs"]["tracked_species"])


def _run_reactor(ct: Any, config: dict[str, Any]) -> dict[str, list[float]]:
    gas = ct.Solution(config["mechanism"])
    gas.TPX = (
        float(config["initial_temperature_k"]),
        float(config["pressure_pa"]),
        config["composition"],
    )
    reactor = ct.IdealGasConstPressureReactor(gas, clone=False)
    sim = ct.ReactorNet([reactor])
    sim.verbose = bool(config["advance"]["verbose"])
    reactor.set_advance_limit(
        "temperature",
        float(config["advance"]["temperature_advance_limit_k"]),
    )

    dt_max = float(config["advance"]["dt_max_s"])
    t_end = float(config["advance"]["t_end_s"])
    species_names = _tracked_species(config)
    profile: dict[str, list[float]] = {
        "time_s": [],
        "time_ms": [],
        "temperature_k": [],
        "pressure_pa": [],
        "internal_energy_j_kg": [],
        "enthalpy_j_kg": [],
    }
    for species in species_names:
        gas.species_index(species)
        profile[f"X_{species}"] = []

    def record_state(time_s_value: float) -> None:
        profile["time_s"].append(float(time_s_value))
        profile["time_ms"].append(float(time_s_value * 1.0e3))
        profile["temperature_k"].append(float(reactor.T))
        profile["pressure_pa"].append(float(reactor.phase.P))
        profile["internal_energy_j_kg"].append(float(reactor.phase.u))
        profile["enthalpy_j_kg"].append(float(reactor.phase.h))
        mole_fractions = reactor.phase.X
        for species_name in species_names:
            profile[f"X_{species_name}"].append(
                float(mole_fractions[gas.species_index(species_name)])
            )

    print(f"{'t [s]':>10s} {'T [K]':>10s} {'P [Pa]':>10s} {'u [J/kg]':>14s}")
    record_state(sim.time)
    print(
        f"{sim.time:10.3e} {reactor.T:10.3f} "
        f"{reactor.phase.P:10.3f} {reactor.phase.u:14.6f}"
    )
    while sim.time < t_end:
        sim.advance(sim.time + dt_max)
        record_state(sim.time)
        print(
            f"{sim.time:10.3e} {reactor.T:10.3f} "
            f"{reactor.phase.P:10.3f} {reactor.phase.u:14.6f}"
        )

    return profile


def _plot_profile(
    plt: Any,
    profile: dict[str, list[float]],
    tracked_species: list[str],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    axes[0, 0].plot(profile["time_ms"], profile["temperature_k"])
    axes[0, 0].set_xlabel("time [ms]")
    axes[0, 0].set_ylabel("temperature [K]")

    for axis, species in zip(axes.flat[1:], tracked_species[:3]):
        axis.plot(profile["time_ms"], profile[f"X_{species}"])
        axis.set_xlabel("time [ms]")
        axis.set_ylabel(f"X_{species}")

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run or dry-run the C01 constant-pressure ignition capability."""
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)

    resolved_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else repo_relative_path(config["outputs"]["output_dir"])
    )

    if dry_run:
        return {
            "capability_id": config["capability_id"],
            "case_id": config["case_id"],
            "output_dir": str(resolved_output_dir),
            "validated_config": True,
            "requires_solver": "cantera>=3.2",
        }

    ct, plt = _import_solver_stack()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_output_dir / "ignition_run.log"
    csv_path = resolved_output_dir / "ignition_profile.csv"
    plot_path = resolved_output_dir / "ignition_temperature_species.png"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            profile = _run_reactor(ct, config)

    tracked_species = _tracked_species(config)
    summary = summarize_profile(
        profile,
        tracked_species,
        ignition_delay_method=config["ignition_delay_method"],
    )

    artifacts: dict[str, str] = {}
    if config["outputs"]["save_csv"]:
        write_profile_csv(csv_path, profile)
        artifacts["ignition_profile.csv"] = str(csv_path)
    if config["outputs"]["save_plots"]:
        _plot_profile(plt, profile, tracked_species, plot_path)
        artifacts["ignition_temperature_species.png"] = str(plot_path)
    if config["outputs"]["save_log"]:
        artifacts["ignition_run.log"] = str(log_path)

    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "profile": profile,
        "summary": summary,
        "artifacts": artifacts,
    }
    if config["outputs"]["save_metrics"]:
        metrics["artifacts"]["metrics.json"] = str(metrics_path)
    if config["outputs"]["save_validation_report"]:
        metrics["artifacts"]["validation_report.md"] = str(report_path)

    pending_validation = {
        "passed": False,
        "checks": [
            {
                "name": "validation.pending",
                "passed": False,
                "details": "Final validation has not been calculated yet.",
            }
        ],
    }
    metrics["validation"] = pending_validation
    if config["outputs"]["save_metrics"]:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if config["outputs"]["save_validation_report"]:
        write_validation_report(report_path, config, metrics, pending_validation)

    validation = validate_metrics(metrics, config, resolved_output_dir)
    metrics["validation"] = validation

    if config["outputs"]["save_metrics"]:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if config["outputs"]["save_validation_report"]:
        write_validation_report(report_path, config, metrics, validation)

    return metrics


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Stable package entrypoint for external workflow callers."""
    return run(config_path=config_path, output_dir=output_dir)
