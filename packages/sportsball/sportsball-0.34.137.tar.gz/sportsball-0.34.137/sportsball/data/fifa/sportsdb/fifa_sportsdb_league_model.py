"""FIFA Sports DB league model."""

from scrapesession.scrapesession import ScrapeSession  # type: ignore

from ...league import League
from ...sportsdb.sportsdb_league_model import SportsDBLeagueModel


class FIFASportsDBLeagueModel(SportsDBLeagueModel):
    """FIFA SportsDB implementation of the league model."""

    def __init__(self, session: ScrapeSession, position: int | None = None) -> None:
        super().__init__(session, "4429", League.FIFA, position=position)

    @classmethod
    def name(cls) -> str:
        return "fifa-sportsdb-league-model"
