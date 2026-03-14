from __future__ import annotations

from datetime import date

from constraints import AdjacentTeamsDifferentDayConstraint, SingleFixtureDomainConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_adjacent(d1: date, d2: date):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")

    c_adj = mk_club("Adj", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)

    a1 = mk_team(c_adj, "Adj1")
    a2 = mk_team(c_adj, "Adj2")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, d1)
    f2 = mk_fixture(a2, c1, d2)
    f3 = mk_fixture(b1, c1, date(2025, 10, 6))
    f4 = mk_fixture(c1, b1, date(2025, 10, 13))
    return mk_league(teams=[a1, a2, b1, c1], fixtures=[f1, f2, f3, f4])


def test_adjacent_teams_different_day_sat() -> None:
    league = _league_for_adjacent(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), AdjacentTeamsDifferentDayConstraint(enabled=True)]
    assert_sat(league, constraints)


def test_adjacent_teams_different_day_unsat() -> None:
    league = _league_for_adjacent(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), AdjacentTeamsDifferentDayConstraint(enabled=True)]
    assert_unsat(league, constraints)
