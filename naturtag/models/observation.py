import attr
from dateutil.parser import parse as parse_date
from datetime import date, datetime
from typing import List, Dict
from uuid import UUID

from pyinaturalist.node_api import get_observation
from naturtag.constants import OBSERVATION_BASE_URL, Coordinates
from naturtag.models import Taxon
from naturtag.validation import convert_coord_pair

kwarg = attr.ib(default=None)
timestamp = attr.ib(converter=parse_date, default=None)


@attr.s
class Observation:
    """A data class containing information about an observation, matching the schema of
    ``GET /observations`` from the iNaturalist API:
    https://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    """

    id: int = kwarg
    partial: bool = kwarg

    cached_votes_total: int = kwarg
    captive: bool = kwarg
    comments_count: int = kwarg
    community_taxon_id: int = kwarg
    created_at: datetime = timestamp
    # created_time_zone: str = kwarg
    description: str = kwarg
    faves_count: int = kwarg
    geoprivacy: str = kwarg  # Enum
    id_please: bool = kwarg
    identifications_count: int = kwarg
    identifications_most_agree: bool = kwarg
    identifications_most_disagree: bool = kwarg
    identifications_some_agree: bool = kwarg
    license_code: str = kwarg  # Enum
    # location: "50.646894,4.360086"
    map_scale: int = kwarg
    mappable: bool = kwarg
    num_identification_agreements: int = kwarg
    num_identification_disagreements: int = kwarg
    oauth_application_id: str = kwarg
    obscured: bool = kwarg
    # observed_on: date = timestamp
    # observed_on_string: datetime = timestamp
    # observed_time_zone: str = kwarg
    out_of_range: bool = kwarg
    owners_identification_from_vision: bool = kwarg
    place_guess: str = kwarg
    positional_accuracy: int = kwarg
    public_positional_accuracy: int = kwarg
    quality_grade: str = kwarg  # Enum
    site_id: int = kwarg
    spam: bool = kwarg
    species_guess: str = kwarg
    time_observed_at: datetime = timestamp
    # time_zone_offset: "+01:00"
    updated_at: datetime = timestamp
    uri: str = kwarg
    uuid: UUID = kwarg

    @classmethod
    def from_id(cls, id: int):
        """ Lookup and create a new Observation object from an ID """
        json = get_observation(id)
        return cls.from_dict(json)

    @classmethod
    def from_dict(cls, json: Dict, partial: bool = False):
        """ Create a new Observation object from an API response """
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(partial=partial, **valid_json)
