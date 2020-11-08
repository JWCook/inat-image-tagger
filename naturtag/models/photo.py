import attr
from pathlib import Path
from typing import List, Dict, Tuple

from naturtag.constants import PHOTO_BASE_URL, PHOTO_INFO_BASE_URL, CC_LICENSES
from naturtag.validation import format_const, format_dimensions

kwarg = attr.ib(default=None)


# TODO: Handle images hosted on other sites (Flickr, Picasa, etc.)
@attr.s
class Photo:
    """A data class containing information about a photo"""
    id: int = kwarg

    attribution: str = kwarg
    flags: List = attr.ib(factory=list)
    license_code: str = attr.ib(converter=format_const, default=None)  # Enum
    original_dimensions: Tuple[int, int] = attr.ib(converter=format_dimensions, factory=dict)
    url: str = kwarg
    _url_format: str = attr.ib(init=False, default=None)

    # Manually construct URLs instead of relying of response, since they are inconsistent;
    # some responses contain URLs of all image sizes, some only contain a single url
    def __attrs_post_init__(self):
        if not self.url:
            return

        # Strip off request params
        path = Path(self.url.rsplit('?', 1)[0])
        # Get a URL format string to get different photo sizes
        self._url_format = f'{PHOTO_BASE_URL}/{self.id}/{{size}}{path.suffix}'
        # Point default URL to info page instead of thumbnail
        self.url = f'{PHOTO_INFO_BASE_URL}/{self.id}'

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

    @property
    def has_cc_license(self) -> bool:
        """Determine if this photo has a Creative Commons license"""
        return self.license_code in CC_LICENSES

    @property
    def thumbnail_url(self) -> str:
        return self._url_format.format(size='square')

    @property
    def small_url(self) -> str:
        return self._url_format.format(size='small')

    @property
    def medium_url(self) -> str:
        return self._url_format.format(size='medium')

    @property
    def large_url(self) -> str:
        return self._url_format.format(size='large')

    @property
    def original_url(self) -> str:
        return self._url_format.format(size='original')
