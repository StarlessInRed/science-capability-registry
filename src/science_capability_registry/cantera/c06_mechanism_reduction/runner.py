"""Runner for the Cantera C06 mechanism reduction capability."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .postprocess import (
    compare_summary,
    plot_temperature_profiles,
    summarize_profile,
    write_profile_csv,
    write_ranking_csv,
    write_reduction_summary_csv,
)
from .report import write_validation_report
from .validation import validate_metrics


def _import_solver_stack() -> tuple[Any, Any, Any]:
    try:
        import cantera as ct
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Cantera is required to execute this capability. Install cantera>=3.2 "
            "in the active environment, then rerun the C06 case."
        ) from exc

    import matplotlib
    import numpy as np

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, np, plt


def _make_initial_gas(ct: Any, config: dict[str, Any]) -> Any:
    gas = ct.Solution(config["mechanism"])
    gas.set_equivalence_ratio(
        float(config["equivalence_ratio"]),
        config["fuel"],
        config["oxidizer"],
    )
    gas.TP = float(config["initial_temperature_k"]), float(config["pressure_pa"])
    return gas


def _make_reactor_network(ct: Any, gas: Any, use_preconditioner: bool) -> tuple[Any, Any]:
    reactor = ct.IdealGasConstPressureMoleReactor(gas, clone=False)
    network = ct.ReactorNet([reactor])
    if use_preconditioner:
        network.preconditioner = ct.AdaptivePreconditioner()
    return reactor, network


def _run_ignition(
    ct: Any,
    np: Any,
    gas: Any,
    end_time_s: float,
    max_steps: int,
    use_preconditioner: bool,
    collect_ranking: bool,
) -> tuple[dict[str, list[float]], Any]:
    reactor, network = _make_reactor_network(ct, gas, use_preconditioner)
    profile: dict[str, list[float]] = {
        "time_ms": [],
        "temperature_k": [],
        "pressure_pa": [],
    }
    reaction_scores = np.zeros(gas.n_reactions) if collect_ranking else None
    step_count = 0
    while network.time < end_time_s:
        network.step()
        step_count += 1
        profile["time_ms"].append(float(1000.0 * network.time))
        profile["temperature_k"].append(float(reactor.T))
        profile["pressure_pa"].append(float(reactor.phase.P))
        if reaction_scores is not None:
            rnet = abs(reactor.phase.net_rates_of_progress)
            max_rate = max(rnet)
            if max_rate > 0.0:
                rnet = rnet / max_rate
                reaction_scores = np.maximum(reaction_scores, rnet)
        if step_count >= max_steps:
            raise RuntimeError(
                f"C06 ignition run exceeded max_steps={max_steps} before end_time_s={end_time_s}."
            )
    return profile, reaction_scores


def _rank_reactions(gas: Any, reaction_scores: Any) -> list[dict[str, Any]]:
    ranked = sorted(
        zip(reaction_scores, gas.reactions()),
        key=lambda pair: -float(pair[0]),
    )
    ranking: list[dict[str, Any]] = []
    for index, (score, reaction) in enumerate(ranked, start=1):
        ranking.append(
            {
                "rank": index,
                "score": float(score),
                "equation": reaction.equation,
                "reaction": reaction,
            }
        )
    return ranking


def _build_reduced_gas(
    ct: Any,
    detailed_gas: Any,
    ranking: list[dict[str, Any]],
    reaction_count: int,
    always_include_species: list[str],
) -> Any:
    selected_reactions = [row["reaction"] for row in ranking[:reaction_count]]
    species_names = set(always_include_species)
    for reaction in selected_reactions:
        species_names.update(reaction.reactants)
        species_names.update(reaction.products)
    species = [detailed_gas.species(name) for name in sorted(species_names)]
    return ct.Solution(
        thermo="ideal-gas",
        kinetics="gas",
        species=species,
        reactions=selected_reactions,
    )


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run or dry-run the C06 mechanism reduction capability."""
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
    ct.suppress_thermo_warnings()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    reduced_dir = resolved_output_dir / "reduced_mechanisms"
    if config["outputs"]["save_reduced_mechanisms"]:
        reduced_dir.mkdir(parents=True, exist_ok=True)

    log_path = resolved_output_dir / "mechanism_reduction_run.log"
    ranking_path = resolved_output_dir / "reaction_ranking.csv"
    reduction_summary_path = resolved_output_dir / "reduction_summary.csv"
    plot_path = resolved_output_dir / "mechanism_reduction_temperature_profiles.png"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"

    artifacts: dict[str, str] = {}

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            detailed_gas = _make_initial_gas(ct, config)
            initial_composition = detailed_gas.mole_fraction_dict()
            print(
                f"Full mechanism species={detailed_gas.n_species} "
                f"reactions={detailed_gas.n_reactions}"
            )
            baseline_profile, reaction_scores = _run_ignition(
                ct,
                np,
                detailed_gas,
                end_time_s=float(config["simulation"]["end_time_s"]),
                max_steps=int(config["simulation"]["max_steps"]),
                use_preconditioner=bool(config["simulation"]["use_adaptive_preconditioner"]),
                collect_ranking=True,
            )
            baseline_summary = summarize_profile(baseline_profile)
            ranking = _rank_reactions(detailed_gas, reaction_scores)

            baseline: dict[str, Any] = {
                "species_count": int(detailed_gas.n_species),
                "reaction_count": int(detailed_gas.n_reactions),
                "summary": baseline_summary,
                "profile": baseline_profile,
            }

            reductions: list[dict[str, Any]] = []
            for reaction_count in config["reduction"]["reaction_counts"]:
                print(f"Building reduced mechanism with {reaction_count} reactions")
                reduced_gas = _build_reduced_gas(
                    ct,
                    detailed_gas,
                    ranking,
                    int(reaction_count),
                    list(config["ranking"]["always_include_species"]),
                )
                mechanism_path = reduced_dir / f"reduced_{reaction_count}_reaction.yaml"
                if config["outputs"]["save_reduced_mechanisms"]:
                    reduced_gas.write_yaml(mechanism_path)
                    artifacts[f"reduced_{reaction_count}_reaction.yaml"] = str(mechanism_path)
                    reloaded_gas = ct.Solution(str(mechanism_path))
                    reload_check = {
                        "loaded": True,
                        "species_count": int(reloaded_gas.n_species),
                        "reaction_count": int(reloaded_gas.n_reactions),
                        "contains_always_include_species": all(
                            name in reloaded_gas.species_names
                            for name in config["ranking"]["always_include_species"]
                        ),
                    }
                else:
                    reload_check = {
                        "loaded": False,
                        "species_count": int(reduced_gas.n_species),
                        "reaction_count": int(reduced_gas.n_reactions),
                        "contains_always_include_species": all(
                            name in reduced_gas.species_names
                            for name in config["ranking"]["always_include_species"]
                        ),
                    }

                reduced_gas.TPX = (
                    float(config["initial_temperature_k"]),
                    float(config["pressure_pa"]),
                    initial_composition,
                )
                profile, _ = _run_ignition(
                    ct,
                    np,
                    reduced_gas,
                    end_time_s=float(config["simulation"]["end_time_s"]),
                    max_steps=int(config["simulation"]["max_steps"]),
                    use_preconditioner=bool(config["simulation"]["use_adaptive_preconditioner"]),
                    collect_ranking=False,
                )
                summary = summarize_profile(profile)
                comparison = compare_summary(baseline_summary, summary)
                reductions.append(
                    {
                        "requested_reaction_count": int(reaction_count),
                        "species_count": int(reduced_gas.n_species),
                        "reaction_count": int(reduced_gas.n_reactions),
                        "time_point_count": int(summary["time_point_count"]),
                        "ignition_delay_ms": float(summary["ignition_delay_ms"]),
                        "ignition_delay_relative_error": comparison[
                            "ignition_delay_relative_error"
                        ],
                        "final_temperature_k": float(summary["final_temperature_k"]),
                        "final_temperature_error_k": comparison[
                            "final_temperature_error_k"
                        ],
                        "summary": summary,
                        "profile": profile,
                        "reload_check": reload_check,
                    }
                )

    ranking_public = [
        {"rank": row["rank"], "score": row["score"], "equation": row["equation"]}
        for row in ranking
    ]

    if config["outputs"]["save_log"]:
        artifacts["mechanism_reduction_run.log"] = str(log_path)
    if config["outputs"]["save_profiles_csv"]:
        baseline_path = resolved_output_dir / "baseline_profile.csv"
        write_profile_csv(baseline_path, baseline["profile"])
        artifacts["baseline_profile.csv"] = str(baseline_path)
        for row in reductions:
            profile_path = resolved_output_dir / f"reduced_{row['requested_reaction_count']}_profile.csv"
            write_profile_csv(profile_path, row["profile"])
            artifacts[f"reduced_{row['requested_reaction_count']}_profile.csv"] = str(
                profile_path
            )
    if config["outputs"]["save_ranking_csv"]:
        write_ranking_csv(ranking_path, ranking_public)
        write_reduction_summary_csv(reduction_summary_path, reductions)
        artifacts["reaction_ranking.csv"] = str(ranking_path)
        artifacts["reduction_summary.csv"] = str(reduction_summary_path)
    if config["outputs"]["save_comparison_plot"]:
        plot_temperature_profiles(plt, baseline, reductions, plot_path)
        artifacts["mechanism_reduction_temperature_profiles.png"] = str(plot_path)

    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "cantera_version": ct.__version__,
        "mechanism": config["mechanism"],
        "baseline": baseline,
        "reaction_ranking": ranking_public,
        "reductions": reductions,
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
