"""
DemandForge package initialization.

This module exposes commonly used project paths:
- ROOT_DIR: the project root directory
- RESULTS_DIR: the default results directory used by fetch/process modules
"""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
RESULTS_DIR = ROOT_DIR / "results"
