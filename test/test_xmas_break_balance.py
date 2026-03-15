from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, XmasBreakBalanceConstraint

from .helpers import assert_all_fixtures_assigned, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


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


def test_xmas_break_balance_solver_dates_sat() -> None:
    """With unassigned dates across a season that spans New Year, teams can be balanced before/after break."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    fixtures = [
        mk_fixture(a1, b1),
        mk_fixture(a1, c1),
        mk_fixture(b1, a1),
        mk_fixture(b1, c1),
        mk_fixture(c1, a1),
        mk_fixture(c1, b1),
    ]
    league = mk_league(teams=[a1, b1, c1], fixtures=fixtures)

    constraints = [
        SingleFixtureDomainConstraint(),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=1.0),
    ]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)


def test_xmas_break_balance_solver_dates_unsat() -> None:
    """Late starts after New Year force all fixtures post-break, violating strict 50/50 balance."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    ca = mk_club("A", va, late_start=date(2026, 1, 6))
    cb = mk_club("B", vb, late_start=date(2026, 1, 6))
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")

    league = mk_league(teams=[a1, b1], fixtures=[mk_fixture(a1, b1), mk_fixture(b1, a1)])
    constraints = [
        SingleFixtureDomainConstraint(),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=1.0),
    ]
    assert_unsat(league, constraints)
