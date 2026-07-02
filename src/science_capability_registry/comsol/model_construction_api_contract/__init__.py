"""COMSOL C02 model construction API contract package."""

from .runner import run, run_from_config

__all__ = ["run", "run_from_config"]
