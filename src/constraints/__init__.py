# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from .adjacent_teams_different_day import AdjacentTeamsDifferentDayConstraint
from .base import CheckResult, Constraint, ConstraintContext, DomainConstraint
from .domain import (
    ClubHolidayDomainConstraint,
    ClubLateStartDomainConstraint,
    create_default_domain_constraints,
    FixedDateDomainConstraint,
    FixtureWeekdayDomainConstraint,
    LeagueHolidayDomainConstraint,
    SameClubDeadlineDomainConstraint,
    TeamHolidayDomainConstraint,
    VenueHolidayDomainConstraint,
)
from .division_day_spread_objective import DivisionDaySpreadObjectiveConstraint
from .first_match_same_club import FirstMatchSameClubConstraint
from .fixture_pair_spacing import FixturePairSpacingConstraint
from .home_away_alternation import HomeAwayAlternationConstraint
from .max_consecutive_weeks import MaxConsecutiveWeeksConstraint
from .only_when import OnlyWhenConstraint
from .single_fixture_domain import SingleFixtureDomainConstraint
from .team_no_overlap_spacing import TeamNoOverlapAndSpacingConstraint
from .venue_assigned_days_objective import VenueAssignedDaysObjectiveConstraint
from .venue_daily_capacity import VenueDailyCapacityConstraint
from .venue_minimize_empty_days_objective import VenueMinimizeEmptyDaysObjectiveConstraint
from .xmas_break_balance import XmasBreakBalanceConstraint

__all__ = [
    "Constraint",
    "CheckResult",
    "ConstraintContext",
    "DomainConstraint",
    "FixtureWeekdayDomainConstraint",
    "ClubLateStartDomainConstraint",
    "LeagueHolidayDomainConstraint",
    "VenueHolidayDomainConstraint",
    "ClubHolidayDomainConstraint",
    "TeamHolidayDomainConstraint",
    "SameClubDeadlineDomainConstraint",
    "FixedDateDomainConstraint",
    "create_default_domain_constraints",
    "SingleFixtureDomainConstraint",
    "TeamNoOverlapAndSpacingConstraint",
    "MaxConsecutiveWeeksConstraint",
    "VenueDailyCapacityConstraint",
    "FirstMatchSameClubConstraint",
    "AdjacentTeamsDifferentDayConstraint",
    "FixturePairSpacingConstraint",
    "OnlyWhenConstraint",
    "HomeAwayAlternationConstraint",
    "XmasBreakBalanceConstraint",
    "VenueAssignedDaysObjectiveConstraint",
    "VenueMinimizeEmptyDaysObjectiveConstraint",
    "DivisionDaySpreadObjectiveConstraint",
]
