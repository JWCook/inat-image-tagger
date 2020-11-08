import attr
from dateutil.parser import parse as parse_date
from datetime import datetime
from typing import List, Dict
from uuid import UUID

from pyinaturalist.node_api import get_observation
from naturtag.constants import Coordinates
from naturtag.models import Photo, Taxon
from naturtag.validation import convert_coord_pair

coordinate_pair = attr.ib(converter=convert_coord_pair, default=None)
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
    description: str = kwarg
    faves_count: int = kwarg
    geoprivacy: str = kwarg  # Enum
    id_please: bool = kwarg
    identifications_count: int = kwarg
    identifications_most_agree: bool = kwarg
    identifications_most_disagree: bool = kwarg
    identifications_some_agree: bool = kwarg
    license_code: str = kwarg  # Enum
    location: Coordinates = coordinate_pair
    map_scale: int = kwarg
    mappable: bool = kwarg
    num_identification_agreements: int = kwarg
    num_identification_disagreements: int = kwarg
    oauth_application_id: str = kwarg
    obscured: bool = kwarg
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
    updated_at: datetime = timestamp
    uri: str = kwarg
    uuid: UUID = attr.ib(converter=UUID, default=None)

    # Nested collections with defaults
    annotations: List = attr.ib(factory=list)
    comments: List = attr.ib(factory=list)  # TODO: make separate model + condensed format
    faves: List = attr.ib(factory=list)
    flags: List = attr.ib(factory=list)
    identifications: List = attr.ib(factory=list)  # TODO: make separate model + condensed format
    ofvs: List = attr.ib(factory=list)
    outlinks: List = attr.ib(factory=list)
    photos: List[Photo] = attr.ib(factory=list, converter=Photo.from_dict_list)
    place_ids: List = attr.ib(factory=list)
    preferences: Dict = attr.ib(factory=dict)
    project_ids: List = attr.ib(factory=list)
    project_ids_with_curator_id: List = attr.ib(factory=list)
    project_ids_without_curator_id: List = attr.ib(factory=list)
    project_observations: List = attr.ib(factory=list)
    quality_metrics: List = attr.ib(factory=list)
    reviewed_by: List = attr.ib(factory=list)
    sounds: List = attr.ib(factory=list)
    tags: List = attr.ib(factory=list)
    taxon: Taxon = attr.ib(factory=Taxon, converter=Taxon.from_dict)
    user: Dict = attr.ib(factory=dict)  # TODO: make separate model + condensed format
    votes: List = attr.ib(factory=list)

    # Additional response fields that are used by the web UI but are redundant here
    # created_at_details: Dict = attr.ib(factory=dict)
    # created_time_zone: str = kwarg
    # geojson: Dict = attr.ib(factory=dict)
    # non_owner_ids: List = attr.ib(factory=list)
    # TODO: Is there any difference between 'observation_photos' and 'photos'?
    # observation_photos: List[Photo] = attr.ib(factory=list, converter=Photo.from_dict_list)
    # observed_on: date = timestamp
    # observed_on_details: Dict = attr.ib(factory=dict)
    # observed_on_string: datetime = timestamp
    # observed_time_zone: str = kwarg
    # time_zone_offset: "+01:00"

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

    @property
    def thumbnail_url(self) -> str:
        if not self.photos:
            return None
        return self.photos[0].get('url')
