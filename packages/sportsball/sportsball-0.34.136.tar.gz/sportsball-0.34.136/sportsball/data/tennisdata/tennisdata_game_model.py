"""Tennisdata game model."""

# pylint: disable=too-many-arguments,duplicate-code
import datetime

import pytest_is_running
from dateutil.parser import parse
from scrapesession.scrapesession import ScrapeSession  # type: ignore

from ...cache import MEMORY
from ..game_model import VERSION as GAME_VERSION
from ..game_model import GameModel
from ..league import League
from ..team_model import VERSION as TEAM_VERSION
from ..venue_model import VERSION
from .tennisdata_team_model import create_tennisdata_team_model
from .tennisdata_venue_model import create_tennisdata_venue_model


def _create_tennisdata_game_model(
    location: str,
    dt: datetime.datetime,
    court: str,
    surface: str,
    best_of: str,
    winner: str,
    loser: str,
    winner_rank: str | None,
    loser_rank: str | None,
    winner_total_points: str | None,
    loser_total_points: str | None,
    winner_points_set_1: str | None,
    loser_points_set_1: str | None,
    winner_points_set_2: str | None,
    loser_points_set_2: str | None,
    winner_points_set_3: str | None,
    loser_points_set_3: str | None,
    winner_points_set_4: str | None,
    loser_points_set_4: str | None,
    winner_points_set_5: str | None,
    loser_points_set_5: str | None,
    winner_sets: str | None,
    loser_sets: str | None,
    winner_odds: str | None,
    loser_odds: str | None,
    session: ScrapeSession,
    league: League,
    version: str,
) -> GameModel:
    winner_team_model = create_tennisdata_team_model(
        name=winner,
        points=int(winner_sets) if winner_sets is not None else None,
        rank=int(winner_rank) if winner_rank is not None else None,
        total_points=int(winner_total_points)
        if winner_total_points is not None
        else None,
        set_one_points=int(winner_points_set_1)
        if winner_points_set_1 is not None
        else None,
        set_two_points=int(winner_points_set_2)
        if winner_points_set_2 is not None
        else None,
        set_three_points=int(winner_points_set_3)
        if winner_points_set_3 is not None
        else None,
        set_four_points=int(winner_points_set_4)
        if winner_points_set_4 is not None
        else None,
        set_five_points=int(winner_points_set_5)
        if winner_points_set_5 is not None
        else None,
        odds=winner_odds,
        session=session,
        dt=dt,
        league=league,
        version=TEAM_VERSION,
    )
    loser_team_model = create_tennisdata_team_model(
        name=loser,
        points=int(loser_sets) if loser_sets is not None else None,
        rank=int(loser_rank) if loser_rank is not None else None,
        total_points=int(loser_total_points)
        if loser_total_points is not None
        else None,
        set_one_points=int(loser_points_set_1)
        if loser_points_set_1 is not None
        else None,
        set_two_points=int(loser_points_set_2)
        if loser_points_set_2 is not None
        else None,
        set_three_points=int(loser_points_set_3)
        if loser_points_set_3 is not None
        else None,
        set_four_points=int(loser_points_set_4)
        if loser_points_set_4 is not None
        else None,
        set_five_points=int(loser_points_set_5)
        if loser_points_set_5 is not None
        else None,
        odds=loser_odds,
        session=session,
        dt=dt,
        league=league,
        version=TEAM_VERSION,
    )
    return GameModel(
        dt=dt,
        week=None,
        game_number=None,
        venue=create_tennisdata_venue_model(
            venue=location,
            session=session,
            dt=dt,
            court=court,
            surface=surface,
            version=VERSION,
        ),
        teams=sorted([winner_team_model, loser_team_model], key=lambda x: x.name),
        end_dt=None,
        attendance=None,
        league=str(league),
        year=None,
        season_type=None,
        postponed=None,
        play_off=None,
        distance=None,
        dividends=[],
        pot=None,
        version=version,
        umpires=[],
        best_of=int(best_of),
    )


@MEMORY.cache(ignore=["session"])
def _cached_create_tennisdata_game_model(
    location: str,
    dt: datetime.datetime,
    court: str,
    surface: str,
    best_of: str,
    winner: str,
    loser: str,
    winner_rank: str | None,
    loser_rank: str | None,
    winner_total_points: str | None,
    loser_total_points: str | None,
    winner_points_set_1: str | None,
    loser_points_set_1: str | None,
    winner_points_set_2: str | None,
    loser_points_set_2: str | None,
    winner_points_set_3: str | None,
    loser_points_set_3: str | None,
    winner_points_set_4: str | None,
    loser_points_set_4: str | None,
    winner_points_set_5: str | None,
    loser_points_set_5: str | None,
    winner_sets: str | None,
    loser_sets: str | None,
    winner_odds: str | None,
    loser_odds: str | None,
    session: ScrapeSession,
    league: League,
    version: str,
) -> GameModel:
    return _create_tennisdata_game_model(
        location=location,
        dt=dt,
        court=court,
        surface=surface,
        best_of=best_of,
        winner=winner,
        loser=loser,
        winner_rank=winner_rank,
        loser_rank=loser_rank,
        winner_total_points=winner_total_points,
        loser_total_points=loser_total_points,
        winner_points_set_1=winner_points_set_1,
        loser_points_set_1=loser_points_set_1,
        winner_points_set_2=winner_points_set_2,
        loser_points_set_2=loser_points_set_2,
        winner_points_set_3=winner_points_set_3,
        loser_points_set_3=loser_points_set_3,
        winner_points_set_4=winner_points_set_4,
        loser_points_set_4=loser_points_set_4,
        winner_points_set_5=winner_points_set_5,
        loser_points_set_5=loser_points_set_5,
        winner_sets=winner_sets,
        loser_sets=loser_sets,
        winner_odds=winner_odds,
        loser_odds=loser_odds,
        session=session,
        league=league,
        version=version,
    )


def create_tennisdata_game_model(
    location: str,
    date: str,
    court: str,
    surface: str,
    best_of: str,
    winner: str,
    loser: str,
    winner_rank: str | None,
    loser_rank: str | None,
    winner_total_points: str | None,
    loser_total_points: str | None,
    winner_points_set_1: str | None,
    loser_points_set_1: str | None,
    winner_points_set_2: str | None,
    loser_points_set_2: str | None,
    winner_points_set_3: str | None,
    loser_points_set_3: str | None,
    winner_points_set_4: str | None,
    loser_points_set_4: str | None,
    winner_points_set_5: str | None,
    loser_points_set_5: str | None,
    winner_sets: str | None,
    loser_sets: str | None,
    winner_odds: str | None,
    loser_odds: str | None,
    session: ScrapeSession,
    league: League,
) -> GameModel:
    """Create a game model based off tennisdata."""
    dt = parse(date)
    if not pytest_is_running.is_running() and dt < datetime.datetime.now().replace(
        tzinfo=dt.tzinfo
    ) - datetime.timedelta(days=7):
        return _cached_create_tennisdata_game_model(
            location=location,
            dt=dt,
            court=court,
            surface=surface,
            best_of=best_of,
            winner=winner,
            loser=loser,
            winner_rank=winner_rank,
            loser_rank=loser_rank,
            winner_total_points=winner_total_points,
            loser_total_points=loser_total_points,
            winner_points_set_1=winner_points_set_1,
            loser_points_set_1=loser_points_set_1,
            winner_points_set_2=winner_points_set_2,
            loser_points_set_2=loser_points_set_2,
            winner_points_set_3=winner_points_set_3,
            loser_points_set_3=loser_points_set_3,
            winner_points_set_4=winner_points_set_4,
            loser_points_set_4=loser_points_set_4,
            winner_points_set_5=winner_points_set_5,
            loser_points_set_5=loser_points_set_5,
            winner_sets=winner_sets,
            loser_sets=loser_sets,
            winner_odds=winner_odds,
            loser_odds=loser_odds,
            session=session,
            league=league,
            version=GAME_VERSION,
        )
    with session.cache_disabled():
        return _create_tennisdata_game_model(
            location=location,
            dt=dt,
            court=court,
            surface=surface,
            best_of=best_of,
            winner=winner,
            loser=loser,
            winner_rank=winner_rank,
            loser_rank=loser_rank,
            winner_total_points=winner_total_points,
            loser_total_points=loser_total_points,
            winner_points_set_1=winner_points_set_1,
            loser_points_set_1=loser_points_set_1,
            winner_points_set_2=winner_points_set_2,
            loser_points_set_2=loser_points_set_2,
            winner_points_set_3=winner_points_set_3,
            loser_points_set_3=loser_points_set_3,
            winner_points_set_4=winner_points_set_4,
            loser_points_set_4=loser_points_set_4,
            winner_points_set_5=winner_points_set_5,
            loser_points_set_5=loser_points_set_5,
            winner_sets=winner_sets,
            loser_sets=loser_sets,
            winner_odds=winner_odds,
            loser_odds=loser_odds,
            session=session,
            league=league,
            version=GAME_VERSION,
        )
