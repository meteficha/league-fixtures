from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, TeamNoOverlapAndSpacingConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_spacing(d1: date, d2: date):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")

    f1 = mk_fixture(ta, tb, d1)
    f2 = mk_fixture(tc, ta, d2)
    f3 = mk_fixture(tb, tc, date(2025, 10, 6))
    return mk_league(teams=[ta, tb, tc], fixtures=[f1, f2, f3])


def test_team_no_overlap_spacing_sat() -> None:
    league = _league_for_spacing(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5)]
    assert_sat(league, constraints)


def test_team_no_overlap_spacing_unsat() -> None:
    league = _league_for_spacing(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5)]
    assert_unsat(league, constraints)
