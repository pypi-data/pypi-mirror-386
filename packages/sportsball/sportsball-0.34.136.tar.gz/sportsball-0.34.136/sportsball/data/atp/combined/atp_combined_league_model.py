"""ATP combined league model."""

# pylint: disable=line-too-long
from scrapesession.scrapesession import ScrapeSession  # type: ignore

from ...combined.combined_league_model import CombinedLeagueModel
from ...league import League
from ..espn.atp_espn_league_model import ATPESPNLeagueModel
from ..tennisabstract.atp_tennisabstract_league_model import \
    ATPTennisAbstractLeagueModel
from ..tennisdata.atp_tennisdata_league_model import ATPTennisDataLeagueModel

ATP_TEAM_IDENTITY_MAP: dict[str, str] = {}
ATP_VENUE_IDENTITY_MAP: dict[str, str] = {}
ATP_PLAYER_IDENTITY_MAP: dict[str, str] = {}


class ATPCombinedLeagueModel(CombinedLeagueModel):
    """ATP combined implementation of the league model."""

    def __init__(self, session: ScrapeSession, league_filter: str | None) -> None:
        super().__init__(
            session,
            League.ATP,
            [
                ATPTennisAbstractLeagueModel(session, position=0),
                ATPESPNLeagueModel(session, position=1),
                ATPTennisDataLeagueModel(session, position=2),
            ],
            league_filter,
        )

    @classmethod
    def team_identity_map(cls) -> dict[str, str]:
        return ATP_TEAM_IDENTITY_MAP

    @classmethod
    def venue_identity_map(cls) -> dict[str, str]:
        return ATP_VENUE_IDENTITY_MAP

    @classmethod
    def player_identity_map(cls) -> dict[str, str]:
        return ATP_PLAYER_IDENTITY_MAP

    @classmethod
    def name(cls) -> str:
        return "atp-combined-league-model"
