# OpenFOAM Physical Trend Checks

Perturbation cases should test whether outputs move in physically expected directions.

## Initial Capability Trends

- C01 lid-driven cavity: increasing Reynolds number should sharpen vortical structures and increase velocity gradients before the laminar assumption becomes invalid.
- C03 backward-facing step RANS: increasing inlet velocity should increase pressure drop and may shift reattachment behavior.
- C06 dam break VOF: gravity magnitude and initial water column height should affect front propagation speed and impact timing.

## Other Useful Trends

- External aerodynamics: drag should respond consistently to inflow speed, angle, and geometry changes.
- Heat transfer: higher temperature difference or heat flux should increase heat transfer rate in the expected direction.
- Compressible shock cases: Mach number changes should alter shock strength and location.

## Review Rule

Trend checks are not a substitute for benchmark reference data, but they catch many wrong boundary conditions, dimensions, signs, and postprocess mistakes.
