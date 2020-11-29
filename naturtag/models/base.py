import attr
from dateutil.parser import parse as parse_date
from logging import getLogger
from typing import Dict, List

aliased_kwarg = attr.ib(default=None, repr=False)
kwarg = attr.ib(default=None)
timestamp = attr.ib(converter=parse_date, default=None)
logger = getLogger(__name__)


@attr.s
class BaseModel:
    id: int = kwarg
    partial: bool = kwarg

    @classmethod
    def from_dict(cls, json: Dict, partial=False):
        """ Create a new model object from all or part of an API response """
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        if not json:
            return cls()
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(**valid_json, partial=partial)

    @classmethod
    def from_dict_list(cls, json: List[Dict]) -> List:
        return [cls.from_dict(p) for p in json]
