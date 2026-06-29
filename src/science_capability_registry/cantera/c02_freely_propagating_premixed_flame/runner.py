"""Runner for the Cantera C02 freely propagating premixed flame capability."""

from __future__ import annotations

import contextlib
import json
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
            "Cantera is required to execute this capability. Install cantera>=3.2 "
            "in the active environment, then rerun the C02 case."
        ) from exc

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, plt


def _configure_flame(ct: Any, config: dict[str, Any]) -> tuple[Any, Any]:
    gas = ct.Solution(config["mechanism"])
    gas.TPX = (
        float(config["unburned_temperature_k"]),
        float(config["pressure_pa"]),
        config["reactants"],
    )
    flame = ct.FreeFlame(gas, width=float(config["width_m"]))
    refine = config["refine_criteria"]
    flame.set_refine_criteria(
        ratio=float(refine["ratio"]),
        slope=float(refine["slope"]),
        curve=float(refine["curve"]),
    )
    return gas, flame


def _snapshot_path(output_dir: Path, hdf_output: bool, mode_name: str) -> tuple[Path, str]:
    if hdf_output:
        return output_dir / "premixed_flame.h5", mode_name
    return output_dir / f"premixed_flame_{mode_name}.yaml", "solution"


def _save_snapshot(
    flame: Any,
    output_dir: Path,
    hdf_output: bool,
    mode_name: str,
    save_enabled: bool,
) -> Path | None:
    if not save_enabled:
        return None
    path, entry = _snapshot_path(output_dir, hdf_output, mode_name)
    flame.save(
        path,
        name=entry,
        description=f"Cantera C02 {mode_name} solution",
        overwrite=True,
    )
    return path


def _plot_temperature_heat_release(plt: Any, profile: dict[str, list[float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grid_mm = [value * 1000.0 for value in profile["grid_m"]]
    fig, ax1 = plt.subplots()
    ax1.plot(grid_mm, [value / 1.0e6 for value in profile["heat_release_rate_w_m3"]], color="C4")
    ax1.set_xlabel("flame coordinate [mm]")
    ax1.set_ylabel("heat release rate [MW/m3]", color="C4")

    ax2 = ax1.twinx()
    ax2.plot(grid_mm, profile["temperature_k"], color="C3")
    ax2.set_ylabel("temperature [K]", color="C3")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_species(
    plt: Any,
    profile: dict[str, list[float]],
    species_names: list[str],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grid_mm = [value * 1000.0 for value in profile["grid_m"]]
    fig, ax = plt.subplots()
    for species in species_names:
        ax.plot(grid_mm, profile[f"X_{species}"], label=species)
    ax.set_xlabel("flame coordinate [mm]")
    ax.set_ylabel("mole fraction")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _mode_species(config: dict[str, Any]) -> list[str]:
    species = list(config["outputs"]["major_species"])
    for name in config["outputs"].get("minor_species", []):
        if name not in species:
            species.append(name)
    return species


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run or dry-run the C02 freely propagating premixed flame capability."""
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)

    requested_modes = [mode["mode"] for mode in config["transport_modes"]]
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
            "requires_solver": "cantera>=3.2",
        }

    ct, plt = _import_solver_stack()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_output_dir / "premixed_flame_run.log"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"
    temperature_plot_path = resolved_output_dir / "premixed_flame_temperature_heat_release.png"
    species_plot_path = resolved_output_dir / "premixed_flame_major_species.png"

    species_names = _mode_species(config)
    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "modes": {},
        "artifacts": {},
    }
    final_profile: dict[str, list[float]] | None = None

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            gas, flame = _configure_flame(ct, config)
            flame.show()

            hdf_output = "native" in ct.hdf_support()
            if hdf_output and config["outputs"]["save_solution_snapshots"]:
                (resolved_output_dir / "premixed_flame.h5").unlink(missing_ok=True)

            for mode_cfg in config["transport_modes"]:
                mode_name = mode_cfg["mode"]
                flame.transport_model = mode_cfg["transport_model"]
                if "flux_gradient_basis" in mode_cfg:
                    flame.flux_gradient_basis = mode_cfg["flux_gradient_basis"]
                flame.soret_enabled = bool(mode_cfg["soret_enabled"])
                flame.solve(
                    loglevel=int(config.get("loglevel", 0)),
                    auto=bool(mode_cfg["auto_solve"]),
                )
                flame.show()
                print(f"{mode_name} flamespeed = {float(flame.velocity[0]):7f} m/s")

                profile = extract_profile(flame, gas, species_names)
                final_profile = profile
                summary = summarize_profile(profile, species_names)
                summary.update(
                    {
                        "converged": True,
                        "transport_model": mode_cfg["transport_model"],
                        "soret_enabled": bool(mode_cfg["soret_enabled"]),
                        "flame_speed_m_s": float(flame.velocity[0]),
                    }
                )

                if config["outputs"]["save_csv"]:
                    csv_path = resolved_output_dir / f"premixed_flame_{mode_name}.csv"
                    write_profile_csv(csv_path, profile)
                    summary["csv_path"] = str(csv_path)
                    metrics["artifacts"][f"premixed_flame_{mode_name}.csv"] = str(csv_path)

                snapshot_path = _save_snapshot(
                    flame,
                    resolved_output_dir,
                    hdf_output,
                    mode_name,
                    bool(config["outputs"]["save_solution_snapshots"]),
                )
                if snapshot_path is not None:
                    if hdf_output:
                        metrics["artifacts"]["premixed_flame.h5"] = str(snapshot_path)
                    else:
                        metrics["artifacts"][snapshot_path.name] = str(snapshot_path)

                metrics["modes"][mode_name] = summary

    if config["outputs"]["save_log"]:
        metrics["artifacts"]["premixed_flame_run.log"] = str(log_path)

    if config["outputs"]["save_plots"] and final_profile is not None:
        _plot_temperature_heat_release(plt, final_profile, temperature_plot_path)
        _plot_species(plt, final_profile, config["outputs"]["major_species"], species_plot_path)
        metrics["artifacts"]["premixed_flame_temperature_heat_release.png"] = str(
            temperature_plot_path
        )
        metrics["artifacts"]["premixed_flame_major_species.png"] = str(species_plot_path)

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
