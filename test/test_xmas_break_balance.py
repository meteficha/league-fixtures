from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, XmasBreakBalanceConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_xmas(d1: date, d2: date):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")

    f1 = mk_fixture(a1, b1, d1)
    f2 = mk_fixture(b1, a1, d2)
    return mk_league(teams=[a1, b1], fixtures=[f1, f2])


def test_xmas_break_balance_sat() -> None:
    league = _league_for_xmas(date(2025, 10, 6), date(2026, 1, 5))
    constraints = [
        SingleFixtureDomainConstraint(),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=1.0),
    ]
    assert_sat(league, constraints)


def test_xmas_break_balance_unsat() -> None:
    league = _league_for_xmas(date(2025, 10, 6), date(2025, 10, 13))
    constraints = [
        SingleFixtureDomainConstraint(),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=1.0),
    ]
    assert_unsat(league, constraints)
