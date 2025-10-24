"""Footballdata game model."""

# pylint: disable=too-many-arguments,duplicate-code
import datetime
import logging

import pytest_is_running
from dateutil import parser
from dateutil.parser import parse
from scrapesession.scrapesession import ScrapeSession  # type: ignore

from ...cache import MEMORY
from ..game_model import VERSION as GAME_VERSION
from ..game_model import GameModel
from ..league import League
from ..team_model import VERSION as TEAM_VERSION
from ..umpire_model import VERSION as UMPIRE_VERSION
from .footballdata_team_model import create_footballdata_team_model
from .footballdata_umpire_model import create_footballdata_umpire_model


def _create_footballdata_game_model(
    session: ScrapeSession,
    league: League,
    dt: datetime.datetime,
    home_team: str,
    away_team: str,
    full_time_home_goals: str,
    full_time_away_goals: str,
    referee: str | None,
    home_shots: str | None,
    away_shots: str | None,
    home_shots_on_target: str | None,
    away_shots_on_target: str | None,
    home_fouls: str | None,
    away_fouls: str | None,
    home_yellow_cards: str | None,
    away_yellow_cards: str | None,
    home_red_cards: str | None,
    away_red_cards: str | None,
    home_odds: str | None,
    away_odds: str | None,
    draw_odds: str | None,
    version: str,
) -> GameModel:
    home_team_model = create_footballdata_team_model(
        session=session,
        league=league,
        dt=dt,
        name=home_team,
        full_time_goals=full_time_home_goals,
        shots=home_shots,
        shots_on_target=home_shots_on_target,
        fouls=home_fouls,
        yellow_cards=home_yellow_cards,
        red_cards=home_red_cards,
        odds=home_odds,
        draw_odds=draw_odds,
        version=TEAM_VERSION,
    )
    away_team_model = create_footballdata_team_model(
        session=session,
        league=league,
        dt=dt,
        name=away_team,
        full_time_goals=full_time_away_goals,
        shots=away_shots,
        shots_on_target=away_shots_on_target,
        fouls=away_fouls,
        yellow_cards=away_yellow_cards,
        red_cards=away_red_cards,
        odds=away_odds,
        draw_odds=draw_odds,
        version=TEAM_VERSION,
    )
    return GameModel(
        dt=dt,
        week=None,
        game_number=None,
        venue=None,
        teams=[home_team_model, away_team_model],
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
        umpires=[
            create_footballdata_umpire_model(name=referee, version=UMPIRE_VERSION)  # type: ignore
        ]
        if referee is not None
        else [],
        best_of=None,
    )


@MEMORY.cache(ignore=["session"])
def _cached_create_footballdata_game_model(
    session: ScrapeSession,
    league: League,
    dt: datetime.datetime,
    home_team: str,
    away_team: str,
    full_time_home_goals: str,
    full_time_away_goals: str,
    referee: str | None,
    home_shots: str | None,
    away_shots: str | None,
    home_shots_on_target: str | None,
    away_shots_on_target: str | None,
    home_fouls: str | None,
    away_fouls: str | None,
    home_yellow_cards: str | None,
    away_yellow_cards: str | None,
    home_red_cards: str | None,
    away_red_cards: str | None,
    home_odds: str | None,
    away_odds: str | None,
    draw_odds: str | None,
    version: str,
) -> GameModel:
    return _create_footballdata_game_model(
        session=session,
        league=league,
        dt=dt,
        home_team=home_team,
        away_team=away_team,
        full_time_home_goals=full_time_home_goals,
        full_time_away_goals=full_time_away_goals,
        referee=referee,
        home_shots=home_shots,
        away_shots=away_shots,
        home_shots_on_target=home_shots_on_target,
        away_shots_on_target=away_shots_on_target,
        home_fouls=home_fouls,
        away_fouls=away_fouls,
        home_yellow_cards=home_yellow_cards,
        away_yellow_cards=away_yellow_cards,
        home_red_cards=home_red_cards,
        away_red_cards=away_red_cards,
        home_odds=home_odds,
        away_odds=away_odds,
        draw_odds=draw_odds,
        version=version,
    )


def create_footballdata_game_model(
    session: ScrapeSession,
    league: League,
    date: str,
    time: str,
    home_team: str,
    away_team: str,
    full_time_home_goals: str,
    full_time_away_goals: str,
    referee: str | None,
    home_shots: str | None,
    away_shots: str | None,
    home_shots_on_target: str | None,
    away_shots_on_target: str | None,
    home_fouls: str | None,
    away_fouls: str | None,
    home_yellow_cards: str | None,
    away_yellow_cards: str | None,
    home_red_cards: str | None,
    away_red_cards: str | None,
    home_odds: str | None,
    away_odds: str | None,
    draw_odds: str | None,
) -> GameModel:
    """Create a game model based off footballdata."""
    dt = None
    try:
        dt = parse(" ".join([date, time]), dayfirst=False)
    except parser._parser.ParserError as exc:  # type: ignore
        logging.error(str(exc))
        logging.error("%s %s", date, time)
        raise exc
    if not pytest_is_running.is_running() and dt < datetime.datetime.now().replace(
        tzinfo=dt.tzinfo
    ) - datetime.timedelta(days=7):
        return _cached_create_footballdata_game_model(
            session=session,
            league=league,
            dt=dt,
            home_team=home_team,
            away_team=away_team,
            full_time_home_goals=full_time_home_goals,
            full_time_away_goals=full_time_away_goals,
            referee=referee,
            home_shots=home_shots,
            away_shots=away_shots,
            home_shots_on_target=home_shots_on_target,
            away_shots_on_target=away_shots_on_target,
            home_fouls=home_fouls,
            away_fouls=away_fouls,
            home_yellow_cards=home_yellow_cards,
            away_yellow_cards=away_yellow_cards,
            home_red_cards=home_red_cards,
            away_red_cards=away_red_cards,
            home_odds=home_odds,
            away_odds=away_odds,
            draw_odds=draw_odds,
            version=GAME_VERSION,
        )
    with session.cache_disabled():
        return _create_footballdata_game_model(
            session=session,
            league=league,
            dt=dt,
            home_team=home_team,
            away_team=away_team,
            full_time_home_goals=full_time_home_goals,
            full_time_away_goals=full_time_away_goals,
            referee=referee,
            home_shots=home_shots,
            away_shots=away_shots,
            home_shots_on_target=home_shots_on_target,
            away_shots_on_target=away_shots_on_target,
            home_fouls=home_fouls,
            away_fouls=away_fouls,
            home_yellow_cards=home_yellow_cards,
            away_yellow_cards=away_yellow_cards,
            home_red_cards=home_red_cards,
            away_red_cards=away_red_cards,
            home_odds=home_odds,
            away_odds=away_odds,
            draw_odds=draw_odds,
            version=GAME_VERSION,
        )
