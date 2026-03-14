from __future__ import annotations

from datetime import date

from constraints import FirstMatchSameClubConstraint, SingleFixtureDomainConstraint

from .helpers import assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_first_match(same_club_date: date, other_date: date):
    v_main = mk_venue("Main")
    v_other = mk_venue("Other")

    c = mk_club("C", v_main)
    o = mk_club("O", v_other)

    c1 = mk_team(c, "C1")
    c2 = mk_team(c, "C2")
    o1 = mk_team(o, "O1")

    f_same = mk_fixture(c1, c2, same_club_date)
    f_other = mk_fixture(c1, o1, other_date)
    f_balanced = mk_fixture(o1, c1, date(2025, 10, 6))
    f_c2_home = mk_fixture(c2, o1, date(2025, 10, 13))
    return mk_league(teams=[c1, c2, o1], fixtures=[f_same, f_other, f_balanced, f_c2_home])


def test_first_match_same_club_sat() -> None:
    league = _league_for_first_match(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_sat(league, constraints)


def test_first_match_same_club_unsat() -> None:
    league = _league_for_first_match(date(2025, 9, 8), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_unsat(league, constraints)
