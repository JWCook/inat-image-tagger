import attr
from dateutil.parser import parse as parse_date
from datetime import datetime
from typing import List, Dict

aliased_kwarg = attr.ib(default=None, repr=False)
kwarg = attr.ib(default=None)


@attr.s
class User:
    id: int = kwarg

    activity_count: int = kwarg
    created_at: datetime = attr.ib(converter=parse_date, default=None)
    display_name: str = kwarg
    icon: str = kwarg
    icon_url: str = kwarg
    identifications_count: int = kwarg
    journal_posts_count: int = kwarg
    login: str = aliased_kwarg  # Aliased to 'username'
    name: str = aliased_kwarg  # Aliased to 'display_name'
    observations_count: int = kwarg
    orcid: str = kwarg
    roles: List = attr.ib(factory=list)
    site_id: int = kwarg
    spam: bool = kwarg
    suspended: bool = kwarg
    universal_search_rank: int = kwarg
    username: str = kwarg

    # Additional response fields that are used by the web UI but are redundant here
    # login_autocomplete: str = kwarg
    # login_exact: str = kwarg
    # name_autocomplete: str = kwarg

    # Add aliases
    def __attrs_post_init__(self):
        self.username = self.login
        self.display_name = self.name

    @classmethod
    def from_dict(cls, json: Dict):
        """Create a new Photo object from an API response"""
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(**valid_json)
