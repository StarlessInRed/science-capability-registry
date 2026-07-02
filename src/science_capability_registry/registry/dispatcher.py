"""Explicit config-first dispatcher for registered capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from science_capability_registry.cantera.c01_constant_pressure_ignition import run as run_cantera_c01
from science_capability_registry.cantera.c02_freely_propagating_premixed_flame import run as run_cantera_c02
from science_capability_registry.cantera.c03_counterflow_diffusion_flame import run as run_cantera_c03
from science_capability_registry.cantera.c04_extinction_strain_rate import run as run_cantera_c04
from science_capability_registry.cantera.c05_reaction_path_analysis import run as run_cantera_c05
from science_capability_registry.cantera.c06_mechanism_reduction import run as run_cantera_c06
from science_capability_registry.comsol.matlab_server_bridge_runtime import run as run_comsol_c01
from science_capability_registry.gmsh.boundary_layer_size_field_meshing import run as run_gmsh_c05
from science_capability_registry.gmsh.boundary_physical_group_contract import run as run_gmsh_c02
from science_capability_registry.gmsh.cad_import_geometry_healing import run as run_gmsh_c04
from science_capability_registry.gmsh.mesh_refinement_quality_trend import run as run_gmsh_c03
from science_capability_registry.gmsh.multi_solver_mesh_export_contract import run as run_gmsh_c06
from science_capability_registry.gmsh.parametric_geometry_mesh_generation import run as run_gmsh_c01
from science_capability_registry.fluent.external_aero_force_coefficients import run as run_fluent_c04
from science_capability_registry.fluent.heat_transfer_energy_balance import run as run_fluent_c07
from science_capability_registry.fluent.sliding_rotating_mesh import run as run_fluent_c06
from science_capability_registry.fluent.steady_internal_flow_runtime import run as run_fluent_c01
from science_capability_registry.fluent.verification_reference_validation import run as run_fluent_c02
from science_capability_registry.fluent.vof_free_surface_transient import run as run_fluent_c05
from science_capability_registry.fluent.workbench_parameter_integration import run as run_fluent_c08
from science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation import run as run_openfoam_c02
from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow import run as run_openfoam_c03
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step import run as run_openfoam_c08
from science_capability_registry.openfoam.conjugate_heat_transfer_cooling import run as run_openfoam_c07
from science_capability_registry.openfoam.dam_break_vof_free_surface import run as run_openfoam_c06
from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy import run as run_openfoam_c04
from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar import run as run_openfoam_c01
from science_capability_registry.openfoam.transient_cylinder_vortex_shedding import run as run_openfoam_c05

from .catalog import catalog_entries_by_id, load_catalog, repo_path, resolve_capability

Runner = Callable[..., dict[str, Any]]

RUNNERS: dict[str, Runner] = {
    "combustion.cantera.constant_pressure_ignition": run_cantera_c01,
    "combustion.cantera.freely_propagating_premixed_flame": run_cantera_c02,
    "combustion.cantera.counterflow_diffusion_flame": run_cantera_c03,
    "combustion.cantera.extinction_strain_rate": run_cantera_c04,
    "combustion.cantera.reaction_path_analysis": run_cantera_c05,
    "combustion.cantera.mechanism_reduction": run_cantera_c06,
    "cfd.openfoam.lid_driven_cavity_incompressible_laminar": run_openfoam_c01,
    "cfd.openfoam.potential_flow_cylinder_analytical_validation": run_openfoam_c02,
    "cfd.openfoam.backward_facing_step_rans_internal_flow": run_openfoam_c03,
    "cfd.openfoam.external_aero_motorbike_rans_snappy": run_openfoam_c04,
    "cfd.openfoam.transient_cylinder_vortex_shedding": run_openfoam_c05,
    "cfd.openfoam.dam_break_vof_free_surface": run_openfoam_c06,
    "cfd.openfoam.conjugate_heat_transfer_cooling": run_openfoam_c07,
    "cfd.openfoam.compressible_shock_capturing_forward_step": run_openfoam_c08,
    "cfd.fluent.steady_internal_flow_runtime": run_fluent_c01,
    "cfd.fluent.verification_reference_validation": run_fluent_c02,
    "cfd.fluent.external_aero_force_coefficients": run_fluent_c04,
    "cfd.fluent.vof_free_surface_transient": run_fluent_c05,
    "cfd.fluent.sliding_rotating_mesh": run_fluent_c06,
    "cfd.fluent.heat_transfer_energy_balance": run_fluent_c07,
    "cfd.fluent.workbench_parameter_integration": run_fluent_c08,
    "multiphysics.comsol.matlab_server_bridge_runtime": run_comsol_c01,
    "meshing.gmsh.parametric_geometry_mesh_generation": run_gmsh_c01,
    "meshing.gmsh.boundary_physical_group_contract": run_gmsh_c02,
    "meshing.gmsh.mesh_refinement_quality_trend": run_gmsh_c03,
    "meshing.gmsh.cad_import_geometry_healing": run_gmsh_c04,
    "meshing.gmsh.boundary_layer_size_field_meshing": run_gmsh_c05,
    "meshing.gmsh.multi_solver_mesh_export_contract": run_gmsh_c06,
}


def runner_key_set() -> set[str]:
    return set(RUNNERS)


def build_dispatch_plan(catalog_path: str | Path | None = None) -> dict[str, Any]:
    catalog = load_catalog(catalog_path) if catalog_path is not None else load_catalog()
    entries = []
    for capability_id, entry in catalog_entries_by_id(catalog).items():
        entries.append(
            {
                "capability_id": capability_id,
                "software": entry["software"],
                "domain": entry["domain"],
                "run_schema_path": entry["run_schema_path"],
                "default_config_path": entry["default_config_path"],
                "package_entrypoint": entry["package_entrypoint"],
                "benchmark_status": entry["benchmark_status"],
                "dispatch_status": entry["dispatch_status"],
                "current_gate": entry["current_gate"],
                "primary_evidence_id": entry["primary_evidence_id"],
                "runtime_profile_path": entry.get("runtime_profile_path"),
                "benchmark_manifest_path": entry.get("benchmark_manifest_path"),
                "result_contract": entry["result_contract"],
            }
        )
    return {
        "validated_config": True,
        "entries": entries,
        "scope": "dispatch plan only; solver execution remains owned by each capability package",
    }


def run_capability(
    capability_id: str,
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    if capability_id not in RUNNERS:
        raise ValueError(f"Unknown capability_id: {capability_id}")
    entry = resolve_capability(capability_id)
    resolved_config = repo_path(config_path) if config_path is not None else repo_path(entry["default_config_path"])
    if not resolved_config.exists():
        raise FileNotFoundError(f"Capability config_path does not exist: {resolved_config}")
    return RUNNERS[capability_id](config_path=resolved_config, output_dir=output_dir, dry_run=dry_run)
