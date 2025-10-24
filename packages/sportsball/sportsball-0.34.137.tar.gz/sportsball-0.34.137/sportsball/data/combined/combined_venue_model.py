"""Combined venue model."""

from typing import Any

import requests

from ..venue_model import VERSION, VenueModel
from ..wikipedia.wikipedia_venue_model import create_wikipedia_venue_model
from .combined_address_model import create_combined_address_model
from .ffill import ffill
from .most_interesting import more_interesting
from .null_check import is_null


def create_combined_venue_model(
    venue_models: list[VenueModel],
    identifier: str | None,
    session: requests.Session,
    venue_ffill: dict[str, dict[str, Any]],
) -> VenueModel | None:
    """Create a venue model by combining many venue models."""
    if not venue_models or identifier is None:
        return None
    address_model = None
    for venue_model in venue_models:
        address_model = venue_model.address
        if address_model is not None:
            latitude = address_model.latitude
            longitude = address_model.longitude
            if latitude is not None and longitude is not None:
                wikipedia_venue_model = create_wikipedia_venue_model(
                    session,
                    latitude=latitude,
                    longitude=longitude,
                    version=VERSION,
                )
                if wikipedia_venue_model is not None:
                    venue_models.append(wikipedia_venue_model)
                break

    address_models = []
    is_grass = None
    is_indoor = None
    is_turf = None
    is_dirt = None
    is_hard = None
    for venue_model in venue_models:
        venue_model_address = venue_model.address
        if not is_null(venue_model_address):
            address_models.append(venue_model_address)
        is_grass = more_interesting(is_grass, venue_model.is_grass)
        is_indoor = more_interesting(is_indoor, venue_model.is_indoor)
        is_turf = more_interesting(is_turf, venue_model.is_turf)
        is_dirt = more_interesting(is_dirt, venue_model.is_dirt)
        is_hard = more_interesting(is_hard, venue_model.is_hard)

    venue_model = VenueModel.model_construct(
        identifier=identifier,
        name=venue_models[0].name,
        address=create_combined_address_model(address_models),  # type: ignore
        is_grass=is_grass,
        is_indoor=is_indoor,
        is_turf=is_turf,
        is_dirt=is_dirt,
        is_hard=is_hard,
        version=VERSION,
    )

    ffill(venue_ffill, identifier, venue_model)

    return venue_model
