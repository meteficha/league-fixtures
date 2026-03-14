from __future__ import annotations

from datetime import date

from constraints import (
    DivisionDaySpreadObjectiveConstraint,
    SingleFixtureDomainConstraint,
    TeamNoOverlapAndSpacingConstraint,
)

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _sat_league():
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, date(2025, 9, 1))
    f2 = mk_fixture(a1, c1, date(2025, 9, 8))
    f3 = mk_fixture(b1, c1, date(2025, 10, 6))
    f4 = mk_fixture(c1, b1, date(2025, 10, 13))
    return mk_league(teams=[a1, b1, c1], fixtures=[f1, f2, f3, f4])


def _unsat_league():
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, date(2025, 9, 1))
    f2 = mk_fixture(c1, a1, date(2025, 9, 1))
    f3 = mk_fixture(b1, c1, date(2025, 10, 6))
    return mk_league(teams=[a1, b1, c1], fixtures=[f1, f2, f3])


def test_division_day_spread_objective_sat() -> None:
    constraints = [SingleFixtureDomainConstraint(), DivisionDaySpreadObjectiveConstraint()]
    assert_sat(_sat_league(), constraints)


def test_division_day_spread_objective_unsat_with_hard_constraint() -> None:
    constraints = [
        SingleFixtureDomainConstraint(),
        TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5),
        DivisionDaySpreadObjectiveConstraint(),
    ]
    assert_unsat(_unsat_league(), constraints)
