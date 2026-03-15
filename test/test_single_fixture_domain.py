from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, TeamNoOverlapAndSpacingConstraint

from .helpers import assert_all_fixtures_assigned, assert_check_score, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def test_single_fixture_domain_sat() -> None:
    v1 = mk_venue("V1")
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1)
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")

    f1 = mk_fixture(t1, t2, date(2025, 9, 1))
    f2 = mk_fixture(t2, t1, date(2025, 9, 8))
    league = mk_league(teams=[t1, t2], fixtures=[f1, f2])

    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=1)]
    assert_sat(league, constraints)
    assert_check_score(constraints[0], league, expected=1.0)


def test_single_fixture_domain_unsat_empty_domain() -> None:
    blocked_day = date(2025, 9, 1)
    v1 = mk_venue("V1")
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1)
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")
    t1.calendar = t1.calendar.__class__([blocked_day])

    f1 = mk_fixture(t1, t2, blocked_day)
    f2 = mk_fixture(t2, t1, date(2025, 9, 8))
    league = mk_league(teams=[t1, t2], fixtures=[f1, f2])

    assert_unsat(league, [SingleFixtureDomainConstraint()])


def test_single_fixture_domain_solver_dates_sat() -> None:
    """Multiple domain filters can still leave legal dates for unassigned fixtures that the solver can pick."""
    v1 = mk_venue("V1", holidays=[date(2025, 9, 8)])
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1, late_start=date(2025, 9, 8), holidays=[date(2025, 9, 22)])
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")

    f1 = mk_fixture(t1, t2)
    f2 = mk_fixture(t2, t1)
    league = mk_league(
        teams=[t1, t2],
        fixtures=[f1, f2],
        start=date(2025, 9, 1),
        end=date(2025, 10, 27),
        league_holidays=[date(2025, 9, 29)],
    )

    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=1)]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f1.date is not None
    assert f1.date not in {date(2025, 9, 8), date(2025, 9, 22), date(2025, 9, 29)}
    assert f1.date >= date(2025, 9, 8)
    assert_check_score(constraints[0], league, expected=1.0)


def test_single_fixture_domain_solver_dates_unsat_combined_filters() -> None:
    """Late start plus venue/league/club holidays can remove every legal Monday for an unassigned fixture."""
    v1 = mk_venue("V1", holidays=[date(2025, 9, 8)])
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1, late_start=date(2025, 9, 8), holidays=[date(2025, 9, 22)])
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")

    league = mk_league(
        teams=[t1, t2],
        fixtures=[mk_fixture(t1, t2)],
        start=date(2025, 9, 1),
        end=date(2025, 9, 29),
        league_holidays=[date(2025, 9, 15)],
    )

    assert_unsat(league, [SingleFixtureDomainConstraint()])


def test_single_fixture_domain_check_partial_score() -> None:
    """One fixture is on an allowed weekday and one is not, producing a partial domain score."""
    v1 = mk_venue("V1")
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1)
    c2 = mk_club("C2", v2)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")

    league = mk_league(
        teams=[t1, t2],
        fixtures=[
            mk_fixture(t1, t2, date(2025, 9, 1)),
            mk_fixture(t2, t1, date(2025, 9, 9)),
        ],
    )

    result = SingleFixtureDomainConstraint().check(league)
    assert 0.0 < result.score < 1.0
