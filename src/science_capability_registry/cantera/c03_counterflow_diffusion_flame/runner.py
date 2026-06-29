"""Runner for the Cantera C03 counterflow diffusion flame capability."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .postprocess import extract_profile, summarize_profile, write_profile_csv
from .report import write_validation_report
from .validation import validate_metrics


def _import_solver_stack() -> tuple[Any, Any]:
    try:
        import cantera as ct
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Cantera is required to execute this capability. Install it in the active "
            "environment, for example with `conda install -c conda-forge cantera`, "
            "then rerun the C03 case."
        ) from exc

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, plt


def _mode_by_name(config: dict[str, Any], mode_name: str) -> dict[str, Any] | None:
    for mode in config["radiation_modes"]:
        if mode["mode"] == mode_name:
            return mode
    return None


def _configure_flame(ct: Any, config: dict[str, Any]) -> tuple[Any, Any]:
    gas = ct.Solution(config["mechanism"])
    gas.TP = gas.T, float(config["pressure_pa"])
    flame = ct.CounterflowDiffusionFlame(gas, width=float(config["width_m"]))

    fuel = config["fuel_inlet"]
    flame.fuel_inlet.mdot = float(fuel["mass_flux_kg_m2_s"])
    flame.fuel_inlet.X = fuel["composition"]
    flame.fuel_inlet.T = float(fuel["temperature_k"])

    oxidizer = config["oxidizer_inlet"]
    flame.oxidizer_inlet.mdot = float(oxidizer["mass_flux_kg_m2_s"])
    flame.oxidizer_inlet.X = oxidizer["composition"]
    flame.oxidizer_inlet.T = float(oxidizer["temperature_k"])

    refine = config["refine_criteria"]
    flame.set_refine_criteria(
        ratio=float(refine["ratio"]),
        slope=float(refine["slope"]),
        curve=float(refine["curve"]),
        prune=float(refine["prune"]),
    )
    return gas, flame


def _capture_mode(
    flame: Any,
    gas: Any,
    species_names: list[str],
    output_dir: Path,
    mode_name: str,
) -> dict[str, Any]:
    profile = extract_profile(flame, gas, species_names)
    csv_path = output_dir / f"diffusion_flame_{mode_name}.csv"
    write_profile_csv(csv_path, profile)
    summary = summarize_profile(profile, species_names)
    summary.update(
        {
            "converged": True,
            "csv_path": str(csv_path),
        }
    )
    return summary


def _plot_temperatures(plt: Any, profiles: dict[str, dict[str, Any]], output_dir: Path) -> Path:
    figure_path = output_dir / "diffusion_flame_temperature.png"
    fig, ax = plt.subplots()
    if "no_radiation" in profiles:
        ax.plot(
            profiles["no_radiation"]["grid_m"],
            profiles["no_radiation"]["temperature_k"],
            label="Temperature without radiation",
        )
    if "radiation" in profiles:
        ax.plot(
            profiles["radiation"]["grid_m"],
            profiles["radiation"]["temperature_k"],
            label="Temperature with radiation",
        )
    ax.set_title("Counterflow diffusion flame temperature")
    ax.set_xlabel("grid [m]")
    ax.set_ylabel("temperature [K]")
    ax.set_xlim(0.0, max(max(profile["grid_m"]) for profile in profiles.values()))
    ax.set_ylim(0.0, 2500.0)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)
    return figure_path


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run or dry-run the C03 counterflow diffusion flame capability."""
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)

    requested_modes = [mode["mode"] for mode in config["radiation_modes"]]
    resolved_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else repo_relative_path(config["outputs"]["output_dir"])
    )

    if dry_run:
        return {
            "capability_id": config["capability_id"],
            "case_id": config["case_id"],
            "planned_modes": requested_modes,
            "output_dir": str(resolved_output_dir),
            "validated_config": True,
            "requires_solver": "cantera>=3.0",
        }

    ct, plt = _import_solver_stack()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_output_dir / "diffusion_flame_run.log"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"

    species_names = list(config["outputs"]["major_species"])
    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "modes": {},
        "comparisons": {},
        "artifacts": {},
    }
    profile_cache: dict[str, dict[str, Any]] = {}

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            gas, flame = _configure_flame(ct, config)

            no_rad_cfg = _mode_by_name(config, "no_radiation")
            radiation_cfg = _mode_by_name(config, "radiation")

            seed_cfg = no_rad_cfg or {
                "enabled": False,
                "boundary_emissivities": [0.0, 0.0],
            }
            flame.boundary_emissivities = tuple(seed_cfg["boundary_emissivities"])
            flame.radiation_enabled = False
            flame.solve(loglevel=int(config.get("loglevel", 1)), auto=True)
            flame.show_stats()
            if "no_radiation" in requested_modes:
                profile = extract_profile(flame, gas, species_names)
                csv_path = resolved_output_dir / "diffusion_flame_no_radiation.csv"
                write_profile_csv(csv_path, profile)
                profile_cache["no_radiation"] = profile
                summary = summarize_profile(profile, species_names)
                summary.update({"converged": True, "csv_path": str(csv_path)})
                metrics["modes"]["no_radiation"] = summary
                metrics["artifacts"]["diffusion_flame_no_radiation.csv"] = str(csv_path)

            if radiation_cfg is not None:
                flame.boundary_emissivities = tuple(radiation_cfg["boundary_emissivities"])
                flame.radiation_enabled = bool(radiation_cfg["enabled"])
                flame.solve(loglevel=int(config.get("loglevel", 1)), refine_grid=False)
                flame.show_stats()
                profile = extract_profile(flame, gas, species_names)
                csv_path = resolved_output_dir / "diffusion_flame_radiation.csv"
                write_profile_csv(csv_path, profile)
                profile_cache["radiation"] = profile
                summary = summarize_profile(profile, species_names)
                summary.update({"converged": True, "csv_path": str(csv_path)})
                metrics["modes"]["radiation"] = summary
                metrics["artifacts"]["diffusion_flame_radiation.csv"] = str(csv_path)

    metrics["artifacts"]["diffusion_flame_run.log"] = str(log_path)

    if config["outputs"]["save_plots"] and profile_cache:
        figure_path = _plot_temperatures(plt, profile_cache, resolved_output_dir)
        metrics["artifacts"]["diffusion_flame_temperature.png"] = str(figure_path)

    no_rad = metrics["modes"].get("no_radiation")
    radiation = metrics["modes"].get("radiation")
    if no_rad and radiation:
        metrics["comparisons"]["radiation_temperature_drop_k"] = (
            float(no_rad["peak_temperature_k"]) - float(radiation["peak_temperature_k"])
        )

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
