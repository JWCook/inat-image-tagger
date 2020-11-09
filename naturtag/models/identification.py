from typing import Dict, List

from dateutil.parser import parse as parse_date
from datetime import datetime
from uuid import UUID

import attr

from naturtag.models import Taxon, User

kwarg = attr.ib(default=None)
timestamp = attr.ib(converter=parse_date, default=None)


@attr.s
class Identification:
    id: int = kwarg

    body: str = kwarg
    category: str = kwarg  # Enum
    created_at: datetime = timestamp
    current: bool = kwarg
    current_taxon: bool = kwarg
    disagreement: bool = kwarg
    hidden: bool = kwarg
    own_observation: bool = kwarg
    previous_observation_taxon_id: int = kwarg
    spam: bool = kwarg
    taxon_change: bool = kwarg  # TODO: unsure of type
    taxon_id: int = kwarg
    uuid: UUID = attr.ib(converter=UUID, default=None)
    vision: bool = kwarg

    flags: List = attr.ib(factory=list)
    moderator_actions: List = attr.ib(factory=list)
    # observation: {}  # TODO: If this is needed, need to lazy load it
    taxon: Taxon = attr.ib(factory=Taxon, converter=Taxon.from_dict)
    user: User = attr.ib(factory=User, converter=User.from_dict)

    # created_at_details: {}

    @classmethod
    def from_dict(cls, json: Dict):
        """Create a new Photo object from an API response"""
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(**valid_json)

    @classmethod
    def from_dict_list(cls, json: List[Dict]) -> List:
        return [cls.from_dict(p) for p in json]
