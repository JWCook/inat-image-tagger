import attr
from typing import List, Dict

from pyinaturalist.node_api import get_observation
from naturtag.constants import OBSERVATION_BASE_URL

kwarg = attr.ib(default=None)


# TODO
@attr.s
class Observation:
    id: int = kwarg

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
