"""Combined game model."""

# pylint: disable=too-many-locals,line-too-long,too-many-arguments,too-many-branches,too-many-statements,too-many-positional-arguments
import datetime
import logging
from typing import Any

import requests
from pydantic import BaseModel

from ..field_type import TYPE_KEY, FieldType
from ..game_model import VERSION, GameModel
from ..league import League
from ..player_model import PlayerModel
from ..team_model import TeamModel
from ..umpire_model import UmpireModel
from ..venue_model import VenueModel
from .combined_team_model import create_combined_team_model
from .combined_umpire_model import create_combined_umpire_model
from .combined_venue_model import create_combined_venue_model
from .most_interesting import more_interesting
from .normalise_name import normalise_name


def _venue_models(
    game_models: list[GameModel], venue_identity_map: dict[str, str]
) -> tuple[list[VenueModel], str | None]:
    venue_models = []
    full_venue_identity = None
    for game_model in game_models:
        game_model_venue = game_model.venue
        if game_model_venue is not None:
            venue_identity = venue_identity_map.get(game_model_venue.identifier)
            if venue_identity is None:
                logging.warning(
                    "Failed to find %s venue identifier (%s).",
                    game_model_venue.identifier,
                    game_model_venue.name,
                )
            else:
                full_venue_identity = venue_identity
            venue_models.append(game_model_venue)
    return venue_models, full_venue_identity


def _team_models(
    game_models: list[GameModel],
    team_identity_map: dict[str, str],
    player_identity_map: dict[str, str],
    names: dict[str, str],
    coach_names: dict[str, str],
    player_ffill: dict[str, dict[str, Any]],
    team_ffill: dict[str, dict[str, Any]],
    coach_ffill: dict[str, dict[str, Any]],
) -> list[TeamModel]:
    team_models: dict[str, list[TeamModel]] = {}
    for game_model in game_models:
        game_model_teams = game_model.teams
        if game_model_teams:
            for team_model in game_model_teams:
                team_identity = team_identity_map.get(team_model.identifier)
                if team_identity is None:
                    logging.warning(
                        "Failed to find %s team identifier (%s).",
                        team_model.identifier,
                        team_model.name,
                    )
                    team_identity = team_model.identifier
                team_models[team_identity] = team_models.get(team_identity, []) + [
                    team_model
                ]
    return [
        create_combined_team_model(
            v,
            k,
            player_identity_map,
            names,
            coach_names,
            player_ffill,
            team_ffill,
            coach_ffill,
        )  # pyright: ignore
        for k, v in team_models.items()
    ]


def _remove_lookaheads(obj: PlayerModel) -> PlayerModel:
    """Set all fields marked as LOOKAHEAD to None, recursively."""
    if isinstance(obj, BaseModel):
        for name, f in obj.model_fields.items():
            extra = getattr(f, "json_schema_extra", None) or {}
            if extra.get(TYPE_KEY) == FieldType.LOOKAHEAD:
                # validate_assignment=False means this won't revalidate
                setattr(obj, name, None)
            else:
                # Recurse into nested values
                val = getattr(obj, name, None)
                _remove_lookaheads(val)  # type: ignore

    elif isinstance(obj, list):
        for item in obj:  # type: ignore
            _remove_lookaheads(item)

    elif isinstance(obj, dict):
        for v in obj.values():  # type: ignore
            _remove_lookaheads(v)

    return obj


def create_combined_game_model(
    game_models: list[GameModel],
    venue_identity_map: dict[str, str],
    team_identity_map: dict[str, str],
    player_identity_map: dict[str, str],
    session: requests.Session,
    names: dict[str, str],
    coach_names: dict[str, str],
    last_game_number: int | None,
    player_ffill: dict[str, dict[str, Any]],
    team_ffill: dict[str, dict[str, Any]],
    coach_ffill: dict[str, dict[str, Any]],
    umpire_ffill: dict[str, dict[str, Any]],
    team_players_ffill: dict[str, list[PlayerModel]],
    venue_ffill: dict[str, dict[str, Any]],
) -> GameModel:
    """Create a game model by combining many game models."""
    umpires: dict[str, list[UmpireModel]] = {}
    venue_models, full_venue_identity = _venue_models(game_models, venue_identity_map)
    full_team_models = _team_models(
        game_models,
        team_identity_map,
        player_identity_map,
        names,
        coach_names,
        player_ffill,
        team_ffill,
        coach_ffill,
    )
    attendance = None
    end_dt = None
    year = None
    season_type = None
    week = None
    game_number = None
    postponed = None
    play_off = None
    distance = None
    dividends = []
    pot = None
    best_of = None
    dt_votes: dict[str, int] = {}
    for game_model in game_models:
        dt_votes[game_model.dt.isoformat()] = (
            dt_votes.get(game_model.dt.isoformat(), 0) + 1
        )
        attendance = more_interesting(attendance, game_model.attendance)
        end_dt = more_interesting(end_dt, game_model.end_dt)
        year = more_interesting(year, game_model.year)
        season_type = more_interesting(season_type, game_model.season_type)
        week = more_interesting(week, game_model.week)
        game_number = more_interesting(game_number, game_model.game_number)
        postponed = more_interesting(postponed, game_model.postponed)
        play_off = more_interesting(play_off, game_model.play_off)
        distance = more_interesting(distance, game_model.distance)
        dividends.extend(game_model.dividends)
        pot = more_interesting(pot, game_model.pot)
        best_of = more_interesting(best_of, game_model.best_of)
        for umpire_model in game_model.umpires:
            umpire_id = umpire_model.identifier
            umpire_name_key = normalise_name(umpire_model.name)
            if umpire_name_key in names:
                umpire_id = names[umpire_name_key]
            else:
                names[umpire_name_key] = umpire_id
            umpires[umpire_id] = umpires.get(umpire_id, []) + [umpire_model]

    dt = None
    for dt_iso, _ in sorted(dt_votes.items(), key=lambda x: x[1], reverse=True):
        dt = more_interesting(dt, datetime.datetime.fromisoformat(dt_iso))
    if dt is None:
        raise ValueError("dt is null")

    if full_venue_identity is None and venue_models:
        for venue_model in venue_models:
            venue_model_identifier = venue_model.identifier
            if venue_model_identifier is not None:
                full_venue_identity = venue_model_identifier

    if game_number is None and last_game_number is not None:
        game_number = last_game_number + 1

    league = game_models[0].league

    # Forward fill for team player models
    if league in {str(League.NFL), str(League.WNBA), str(League.EPL)}:
        for team_model in full_team_models:
            if team_model.players:
                team_players_ffill[team_model.identifier] = team_model.players
                continue
            team_model.players = [
                _remove_lookaheads(x)
                for x in team_players_ffill.get(team_model.identifier, [])
            ]

    return GameModel.model_construct(
        dt=dt,
        week=week,
        game_number=game_number,
        venue=create_combined_venue_model(
            venue_models, full_venue_identity, session, venue_ffill
        ),  # pyright: ignore
        teams=full_team_models,
        end_dt=end_dt,
        attendance=attendance,
        league=league,
        year=year,
        season_type=season_type,
        postponed=postponed,
        play_off=play_off,
        distance=distance,
        dividends=dividends,
        pot=pot,
        version=VERSION,
        umpires=[
            create_combined_umpire_model(v, k, umpire_ffill) for k, v in umpires.items()
        ],
    )
