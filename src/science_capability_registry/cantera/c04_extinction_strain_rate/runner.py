"""Runner for the Cantera C04 extinction strain rate capability."""

from __future__ import annotations

import contextlib
import csv
import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import validate_metrics


def _import_solver_stack() -> tuple[Any, Any, Any]:
    try:
        import cantera as ct
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Cantera is required to execute this capability. Install cantera>=3.2 "
            "in the active environment, then rerun the C04 case."
        ) from exc

    import matplotlib
    import numpy as np

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, np, plt


def _configure_flame(ct: Any, config: dict[str, Any]) -> Any:
    gas = ct.Solution(config["mechanism"])
    flame = ct.CounterflowDiffusionFlame(gas, width=float(config["width_m"]))
    flame.P = float(config["pressure_pa"])

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
    return flame


def _history_entry(np: Any, flame: Any, alpha: float, status: str) -> dict[str, float | str]:
    max_strain_rate = float(
        np.max(np.abs(np.gradient(flame.velocity) / np.gradient(flame.grid)))
    )
    return {
        "alpha": float(alpha),
        "peak_temperature_k": float(np.max(flame.T)),
        "max_strain_rate_1_s": max_strain_rate,
        "status": status,
    }


def _snapshot_names(output_dir: Path, hdf_output: bool, name: str) -> tuple[Path, str]:
    if hdf_output:
        return output_dir / "flame_data.h5", name
    safe_name = name.replace("-", "_").replace("/", "_")
    return output_dir / f"{safe_name}.yaml", "solution"


def _save_snapshot(
    flame: Any,
    output_dir: Path,
    hdf_output: bool,
    name: str,
    description: str,
    save_enabled: bool,
) -> tuple[Path, str]:
    file_name, entry = _snapshot_names(output_dir, hdf_output, name)
    if save_enabled:
        flame.save(file_name, name=entry, description=description, overwrite=True)
    return file_name, entry


def _write_history_csv(path: Path, history: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["alpha", "peak_temperature_k", "max_strain_rate_1_s", "status"],
        )
        writer.writeheader()
        writer.writerows(history)


def _plot_history(plt: Any, history: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    ax.semilogx(
        [row["max_strain_rate_1_s"] for row in history],
        [row["peak_temperature_k"] for row in history],
    )
    ax.set_xlabel("maximum axial strain rate [1/s]")
    ax.set_ylabel("peak temperature [K]")
    ax.set_title("Extinction strain-rate continuation")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
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

    ct, np, plt = _import_solver_stack()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_output_dir / "diffusion_flame_extinction_run.log"
    history_path = resolved_output_dir / "extinction_summary.csv"
    plot_path = resolved_output_dir / "figure_T_max_a_max.png"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"

    history: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {}
    save_snapshots = bool(config["outputs"]["save_solution_snapshots"])

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            flame = _configure_flame(ct, config)
            temperature_limit_extinction = max(
                float(config["fuel_inlet"]["temperature_k"]),
                float(config["oxidizer_inlet"]["temperature_k"]),
            )

            print("Creating the initial solution")
            flame.solve(loglevel=int(config.get("loglevel", 0)), auto=True)

            hdf_output = "native" in ct.hdf_support()
            if hdf_output and save_snapshots:
                hdf_path = resolved_output_dir / "flame_data.h5"
                hdf_path.unlink(missing_ok=True)

            _save_snapshot(
                flame,
                resolved_output_dir,
                hdf_output,
                "initial-solution",
                "Initial solution",
                save_snapshots,
            )

            alpha = [1.0]
            delta_alpha = float(config["extinction_search"]["initial_delta_alpha"])
            delta_alpha_factor = float(config["extinction_search"]["delta_alpha_factor"])
            delta_alpha_min = float(config["extinction_search"]["delta_alpha_min"])
            delta_temperature_min = float(config["extinction_search"]["delta_temperature_min_k"])
            max_iterations = int(config["extinction_search"]["max_iterations"])
            exponents = config["scaling_exponents"]

            n_last_burning = 0
            history.append(_history_entry(np, flame, alpha[0], "burning"))
            _save_snapshot(
                flame,
                resolved_output_dir,
                hdf_output,
                "extinction/0000",
                "Initial burning solution",
                save_snapshots,
            )

            for n in range(1, max_iterations + 1):
                alpha.append(alpha[n_last_burning] + delta_alpha)
                strain_factor = alpha[-1] / alpha[n_last_burning]

                flame.flame.grid *= strain_factor ** float(exponents["grid"])
                flame.fuel_inlet.mdot *= strain_factor ** float(exponents["mass_flux"])
                flame.oxidizer_inlet.mdot *= strain_factor ** float(exponents["mass_flux"])
                flame.flame.set_values(
                    "velocity",
                    flame.flame.velocity * strain_factor ** float(exponents["velocity"]),
                )
                flame.flame.set_values(
                    "spreadRate",
                    flame.flame.spread_rate * strain_factor ** float(exponents["spread_rate"]),
                )
                flame.flame.set_values(
                    "Lambda",
                    flame.flame.radial_pressure_gradient
                    * strain_factor ** float(exponents["radial_pressure_gradient"]),
                )

                try:
                    flame.solve(loglevel=int(config.get("loglevel", 0)))
                except ct.CanteraError as exc:
                    print("Error: Did not converge at n =", n, exc)

                peak_temperature = float(np.max(flame.T))
                burning = not np.isclose(peak_temperature, temperature_limit_extinction)
                history.append(
                    _history_entry(np, flame, alpha[-1], "burning" if burning else "extinguished")
                )

                if burning:
                    n_last_burning = n
                    _save_snapshot(
                        flame,
                        resolved_output_dir,
                        hdf_output,
                        f"extinction/{n:04d}",
                        f"Solution at alpha = {alpha[-1]}",
                        save_snapshots,
                    )
                    print(
                        "Flame burning at alpha = {:8.4F}. Proceeding to the next "
                        "iteration, with delta_alpha = {}".format(alpha[-1], delta_alpha)
                    )
                    continue

                previous_temperature = float(history[-2]["peak_temperature_k"])
                if (
                    previous_temperature - peak_temperature < delta_temperature_min
                    and delta_alpha < delta_alpha_min
                ):
                    _save_snapshot(
                        flame,
                        resolved_output_dir,
                        hdf_output,
                        f"extinction/{n:04d}",
                        f"Flame extinguished at alpha={alpha[-1]}",
                        save_snapshots,
                    )
                    print(
                        "Flame extinguished at alpha = {0:8.4F}. Abortion criterion "
                        "satisfied.".format(alpha[-1])
                    )
                    break

                delta_alpha = delta_alpha / delta_alpha_factor
                print(
                    "Flame extinguished at alpha = {0:8.4F}. Restoring alpha = "
                    "{1:8.4F} and trying delta_alpha = {2}".format(
                        alpha[-1], alpha[n_last_burning], delta_alpha
                    )
                )
                file_name, entry = _snapshot_names(
                    resolved_output_dir, hdf_output, f"extinction/{n_last_burning:04d}"
                )
                flame.restore(file_name, entry)
            else:
                raise RuntimeError(
                    f"C04 extinction search exceeded max_iterations={max_iterations}."
                )

            file_name, entry = _snapshot_names(
                resolved_output_dir, hdf_output, f"extinction/{n_last_burning:04d}"
            )
            flame.restore(file_name, entry)

            strain_rates = {
                "mean": float(flame.strain_rate("mean")),
                "max": float(flame.strain_rate("max")),
                "potential_flow_fuel": float(flame.strain_rate("potential_flow_fuel")),
                "potential_flow_oxidizer": float(flame.strain_rate("potential_flow_oxidizer")),
                "stoichiometric": float(
                    flame.strain_rate(
                        "stoichiometric",
                        fuel=config.get("stoichiometric_fuel_species", "H2"),
                    )
                ),
            }
            final_peak_temperature = float(np.max(flame.T))

            print("----------------------------------------------------------------------")
            print("Parameters at the extinction point:")
            print("Pressure p={0} bar".format(flame.P / 1e5))
            print("Peak temperature T={0:4.0f} K".format(final_peak_temperature))
            print("Mean axial strain rate a_mean={0:.2e} 1/s".format(strain_rates["mean"]))
            print("Maximum axial strain rate a_max={0:.2e} 1/s".format(strain_rates["max"]))
            print(
                "Fuel inlet potential flow axial strain rate a_fuel={0:.2e} 1/s".format(
                    strain_rates["potential_flow_fuel"]
                )
            )
            print(
                "Oxidizer inlet potential flow axial strain rate a_ox={0:.2e} 1/s".format(
                    strain_rates["potential_flow_oxidizer"]
                )
            )
            print(
                "Axial strain rate at stoichiometric surface a_stoich={0:.2e} 1/s".format(
                    strain_rates["stoichiometric"]
                )
            )

    artifacts["diffusion_flame_extinction_run.log"] = str(log_path)
    if config["outputs"]["save_csv"]:
        _write_history_csv(history_path, history)
        artifacts["extinction_summary.csv"] = str(history_path)
    if config["outputs"]["save_plots"]:
        _plot_history(plt, history, plot_path)
        artifacts["figure_T_max_a_max.png"] = str(plot_path)
    if save_snapshots:
        snapshot_path = resolved_output_dir / "flame_data.h5"
        if not snapshot_path.exists():
            snapshot_path = resolved_output_dir
        artifacts["solution_snapshots"] = str(snapshot_path)

    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "iteration_count": len(history) - 1,
        "history": {
            "alpha": [row["alpha"] for row in history],
            "peak_temperature_k": [row["peak_temperature_k"] for row in history],
            "max_strain_rate_1_s": [row["max_strain_rate_1_s"] for row in history],
            "status": [row["status"] for row in history],
        },
        "extinction": {
            "alpha": float(alpha[n_last_burning]),
            "peak_temperature_k": final_peak_temperature,
            "strain_rates_1_s": strain_rates,
        },
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
    return run(config_path=config_path, output_dir=output_dir)

