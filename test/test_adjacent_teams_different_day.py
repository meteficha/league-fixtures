from __future__ import annotations

from datetime import date

from constraints import AdjacentTeamsDifferentDayConstraint, SingleFixtureDomainConstraint

from .helpers import assert_all_fixtures_assigned, assert_check_score, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


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
    assert_check_score(constraints[1], league, expected=1.0)


def test_adjacent_teams_different_day_unsat() -> None:
    league = _league_for_adjacent(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), AdjacentTeamsDifferentDayConstraint(enabled=True)]
    assert_unsat(league, constraints)


def test_adjacent_teams_different_day_solver_dates_sat() -> None:
    """With 2 adjacent teams and multiple Mondays, the solver can place their external fixtures on different days.

    Fixed filler fixtures are included so every team has at least one home fixture, which is required by SingleFixtureDomainConstraint.
    """
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

    f1 = mk_fixture(a1, b1)
    f2 = mk_fixture(a2, c1)
    f3 = mk_fixture(b1, c1, date(2025, 9, 8))
    f4 = mk_fixture(c1, b1, date(2025, 9, 15))
    league = mk_league(
        teams=[a1, a2, b1, c1],
        fixtures=[f1, f2, f3, f4],
        start=date(2025, 9, 1),
        end=date(2025, 9, 22),
    )

    constraints = [SingleFixtureDomainConstraint(), AdjacentTeamsDifferentDayConstraint(enabled=True)]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f1.date != f2.date
    assert_check_score(constraints[1], league, expected=1.0)


def test_adjacent_teams_different_day_solver_dates_unsat() -> None:
    """With only one legal Monday, AllDifferent on adjacent teams' external fixtures is impossible.

    Fixed filler fixtures keep every team represented with at least one home fixture.
    """
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

    fixtures = [
        mk_fixture(a1, b1),
        mk_fixture(a2, c1),
        mk_fixture(b1, c1, date(2025, 9, 1)),
        mk_fixture(c1, b1, date(2025, 9, 1)),
    ]
    league = mk_league(
        teams=[a1, a2, b1, c1],
        fixtures=fixtures,
        start=date(2025, 9, 1),
        end=date(2025, 9, 8),
    )

    constraints = [SingleFixtureDomainConstraint(), AdjacentTeamsDifferentDayConstraint(enabled=True)]
    assert_unsat(league, constraints)


def test_adjacent_teams_different_day_check_partial_score() -> None:
    """One adjacent pair collides and another does not, so check score is strictly between 0 and 1."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    vd = mk_venue("VD")

    c_adj = mk_club("Adj", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    cd = mk_club("D", vd)

    a1 = mk_team(c_adj, "Adj1")
    a2 = mk_team(c_adj, "Adj2")
    a3 = mk_team(c_adj, "Adj3")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")
    d1 = mk_team(cd, "D1")

    league = mk_league(
        teams=[a1, a2, a3, b1, c1, d1],
        fixtures=[
            mk_fixture(a1, b1, date(2025, 9, 1)),
            mk_fixture(a2, c1, date(2025, 9, 1)),
            mk_fixture(a3, d1, date(2025, 9, 8)),
        ],
    )

    result = AdjacentTeamsDifferentDayConstraint(enabled=True).check(league)
    assert 0.0 < result.score < 1.0
