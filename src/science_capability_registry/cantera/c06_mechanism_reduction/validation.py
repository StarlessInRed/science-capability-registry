"""Automatic validation for Cantera C06 outputs."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _in_range(value: float, limits: dict[str, float]) -> bool:
    return float(limits["min"]) <= value <= float(limits["max"])


def _expected_artifacts(config: dict[str, Any]) -> list[str]:
    outputs = config["outputs"]
    expected: list[str] = []
    if outputs["save_profiles_csv"]:
        expected.append("baseline_profile.csv")
        for count in config["reduction"]["reaction_counts"]:
            expected.append(f"reduced_{count}_profile.csv")
    if outputs["save_ranking_csv"]:
        expected.append("reaction_ranking.csv")
        expected.append("reduction_summary.csv")
    if outputs["save_reduced_mechanisms"]:
        for count in config["reduction"]["reaction_counts"]:
            expected.append(f"reduced_{count}_reaction.yaml")
    if outputs["save_comparison_plot"]:
        expected.append("mechanism_reduction_temperature_profiles.png")
    if outputs["save_log"]:
        expected.append("mechanism_reduction_run.log")
    if outputs["save_metrics"]:
        expected.append("metrics.json")
    if outputs["save_validation_report"]:
        expected.append("validation_report.md")
    return expected


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    limits = config["validation"]
    baseline = metrics.get("baseline", {})
    reductions = metrics.get("reductions", [])
    ranking = metrics.get("reaction_ranking", [])

    full_species = int(baseline.get("species_count", 0))
    full_reactions = int(baseline.get("reaction_count", 0))
    full_summary = baseline.get("summary", {})
    full_final_temperature = float(full_summary.get("final_temperature_k", math.nan))
    full_rise = float(full_summary.get("temperature_rise_k", math.nan))
    full_points = int(full_summary.get("time_point_count", 0))

    _check(
        checks,
        "full.species_count",
        full_species >= int(limits["full_species_count"]["min"]),
        f"Full mechanism species count is {full_species}.",
    )
    _check(
        checks,
        "full.reaction_count",
        full_reactions >= int(limits["full_reaction_count"]["min"]),
        f"Full mechanism reaction count is {full_reactions}.",
    )
    _check(
        checks,
        "full.profile_points",
        full_points >= int(limits["min_profile_points"]),
        f"Full profile point count is {full_points}.",
    )
    _check(
        checks,
        "full.final_temperature",
        _in_range(full_final_temperature, limits["full_final_temperature_k"]),
        f"Full final temperature is {full_final_temperature:.6g} K.",
    )
    _check(
        checks,
        "full.temperature_rise",
        math.isfinite(full_rise) and full_rise >= float(limits["min_temperature_rise_k"]),
        f"Full temperature rise is {full_rise:.6g} K.",
    )
    _check(
        checks,
        "ranking.length",
        len(ranking) >= int(limits["min_ranked_reaction_count"]),
        f"Ranked reaction count is {len(ranking)}.",
    )
    scores_finite = all(math.isfinite(float(row.get("score", math.nan))) for row in ranking)
    sorted_descending = all(
        float(ranking[index]["score"]) >= float(ranking[index + 1]["score"])
        for index in range(len(ranking) - 1)
    )
    _check(checks, "ranking.scores_finite", scores_finite, "Ranking scores are finite.")
    _check(checks, "ranking.sorted", sorted_descending, "Ranking scores are sorted descending.")

    expected_counts = list(config["reduction"]["reaction_counts"])
    observed_counts = [int(row.get("requested_reaction_count", 0)) for row in reductions]
    _check(
        checks,
        "reduced.case_count",
        len(reductions) >= int(limits["min_reduced_case_count"]),
        f"Reduced case count is {len(reductions)}.",
    )
    _check(
        checks,
        "reduced.requested_counts",
        observed_counts == expected_counts,
        f"Observed reaction counts are {observed_counts}.",
    )

    for row in reductions:
        count = int(row.get("requested_reaction_count", 0))
        species_count = int(row.get("species_count", 0))
        reaction_count = int(row.get("reaction_count", 0))
        points = int(row.get("time_point_count", 0))
        ignition_error = float(row.get("ignition_delay_relative_error", math.nan))
        final_error = float(row.get("final_temperature_error_k", math.nan))
        reload_check = row.get("reload_check", {})
        _check(
            checks,
            f"reduced.{count}.reaction_count",
            reaction_count == count,
            f"Reduced mechanism has {reaction_count} reactions.",
        )
        _check(
            checks,
            f"reduced.{count}.species_count",
            species_count >= len(config["ranking"]["always_include_species"]),
            f"Reduced mechanism has {species_count} species.",
        )
        _check(
            checks,
            f"reduced.{count}.profile_points",
            points >= int(limits["min_profile_points"]),
            f"Reduced profile point count is {points}.",
        )
        _check(
            checks,
            f"reduced.{count}.errors_finite",
            math.isfinite(ignition_error) and math.isfinite(final_error),
            f"tau error={ignition_error:.6g}, final T error={final_error:.6g} K.",
        )
        if config["outputs"]["save_reduced_mechanisms"]:
            _check(
                checks,
                f"reduced.{count}.yaml_reload",
                bool(reload_check.get("loaded", False))
                and int(reload_check.get("reaction_count", -1)) == count
                and bool(reload_check.get("contains_always_include_species", False)),
                f"Reload check: {reload_check}.",
            )

    largest_count = int(limits["largest_reduced_reaction_count"])
    largest = next(
        (row for row in reductions if int(row.get("requested_reaction_count", 0)) == largest_count),
        None,
    )
    _check(
        checks,
        "largest_reduced.present",
        largest is not None,
        f"Largest reduced mechanism count is {largest_count}.",
    )
    if largest is not None:
        ignition_error = float(largest.get("ignition_delay_relative_error", math.inf))
        final_error = float(largest.get("final_temperature_error_k", math.inf))
        _check(
            checks,
            "largest_reduced.ignition_delay_error",
            ignition_error
            <= float(limits["largest_reduced_max_ignition_delay_relative_error"]),
            f"Largest reduced ignition delay relative error is {ignition_error:.6g}.",
        )
        _check(
            checks,
            "largest_reduced.final_temperature_error",
            final_error <= float(limits["largest_reduced_max_final_temperature_error_k"]),
            f"Largest reduced final temperature error is {final_error:.6g} K.",
        )

    if output_dir is not None:
        artifacts = metrics.get("artifacts", {})
        for artifact_name in _expected_artifacts(config):
            artifact_path = artifacts.get(artifact_name)
            path = Path(artifact_path) if artifact_path else Path(output_dir) / artifact_name
            if not path.is_absolute():
                path = Path(output_dir) / path
            exists = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.{artifact_name}", exists, f"Artifact path: {path}")

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
