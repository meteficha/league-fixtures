from __future__ import annotations

import sys
from pathlib import Path

import pycsp3.classes.entities as pycsp3ce
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import solver_pycsp3  # noqa: E402


@pytest.fixture(autouse=True)
def reset_solver_state() -> None:
    solver_pycsp3.Solver.created = False
    pycsp3ce.clear()
    yield
    solver_pycsp3.Solver.created = False
    pycsp3ce.clear()
