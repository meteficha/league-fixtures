from __future__ import annotations

from datetime import date

from constraints import HomeAwayAlternationConstraint, SingleFixtureDomainConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_alternation(home_dates: tuple[date, date], away_dates: tuple[date, date]):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")

    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)

    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, home_dates[0])
    f2 = mk_fixture(a1, c1, home_dates[1])
    f3 = mk_fixture(b1, a1, away_dates[0])
    f4 = mk_fixture(c1, a1, away_dates[1])

    return mk_league(teams=[a1, b1, c1], fixtures=[f1, f2, f3, f4])


def test_home_away_alternation_sat() -> None:
    league = _league_for_alternation(
        home_dates=(date(2025, 9, 1), date(2025, 9, 15)),
        away_dates=(date(2025, 9, 8), date(2025, 9, 22)),
    )
    constraints = [SingleFixtureDomainConstraint(), HomeAwayAlternationConstraint(strictHomeAwayConstraint=1)]
    assert_sat(league, constraints)


def test_home_away_alternation_unsat() -> None:
    league = _league_for_alternation(
        home_dates=(date(2025, 9, 1), date(2025, 9, 8)),
        away_dates=(date(2025, 9, 22), date(2025, 9, 29)),
    )
    constraints = [SingleFixtureDomainConstraint(), HomeAwayAlternationConstraint(strictHomeAwayConstraint=1)]
    assert_unsat(league, constraints)
