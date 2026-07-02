from __future__ import annotations

from science_capability_registry.fluent.steady_internal_flow_runtime.validation import (
    parse_mass_flow_reports,
    parse_residual_rows,
    summarize_mass_balance,
)


SAMPLE_TRANSCRIPT = """
  iter  continuity  x-velocity  y-velocity      energy           k     epsilon  surf-mon-1     time/iter
    90  9.3815e-04  4.8916e-06  1.5505e-05  7.0102e-07  9.6091e-06  1.3013e-05  2.9609e+02  0:00:00    1
!   90 solution is converged
    91  8.8669e-04  4.5380e-06  1.5038e-05  6.4810e-07  9.1726e-06  1.3172e-05  2.9609e+02  0:00:00    0
!   91 solution is converged
                  Mass Flow Rate               [kg/s]
-------------------------------- --------------------
                      internal-3            2435.2227
               pressure-outlet-7           -284.47867
                velocity-inlet-5               162.56
                velocity-inlet-6            121.92006
                          wall-4                   -0
                          wall-8                   -0
                ---------------- --------------------
                             Net         0.0013923645
"""


def test_parse_residual_rows_extracts_final_residuals() -> None:
    rows = parse_residual_rows(SAMPLE_TRANSCRIPT)

    assert len(rows) == 2
    assert rows[-1]["iteration"] == 91
    assert rows[-1]["continuity"] == 8.8669e-04
    assert rows[-1]["energy"] == 6.4810e-07


def test_parse_mass_flow_report_and_selected_imbalance() -> None:
    reports = parse_mass_flow_reports(SAMPLE_TRANSCRIPT)
    config = {
        "reports": {
            "mass_flow": {
                "inlet_zones": ["velocity-inlet-5", "velocity-inlet-6"],
                "outlet_zones": ["pressure-outlet-7"],
            }
        }
    }
    summary = summarize_mass_balance(reports[-1], config)

    assert len(reports) == 1
    assert summary["inlet_mass_flow_kg_s"] == 284.48006
    assert summary["outlet_mass_flow_kg_s"] == -284.47867
    assert summary["mass_imbalance_fraction"] < 1.0e-5
