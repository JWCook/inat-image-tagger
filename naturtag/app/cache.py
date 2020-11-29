""" UI-specific utilities for image caching """
from logging import getLogger

from kivy.core.image import Image

from naturtag.atlas import get_resource_path_if_exists
from naturtag.thumbnails import (
    generate_thumbnail_from_bytes,
    get_thumbnail,
    get_thumbnail_hash,
    get_thumbnail_if_exists,
    to_monochrome,
)

logger = getLogger().getChild(__name__)


def cache_async_thumbnail(async_image, **kwargs):
    """
    Get raw image data from an AsyncImage and cache a thumbnail for future usage.
    See :py:func:`.generate_thumbnail` for size options.

    Args:
        async_image (:py:class:`~kivy.uix.image.AsyncImage`): Image object

    Returns:
        str: The path of the new thumbnail
    """
    image_bytes, _ = async_image.get_image_bytes()
    generate_thumbnail_from_bytes(image_bytes, async_image.source, **kwargs)


def get_any_thumbnail(source: str, size: str = 'small') -> str:
    """ Get the path of a thumbnail stored inside either an atlas or the thumbnail cache """
    return get_atlas_thumbnail_if_exists(source, size) or get_thumbnail(source)


def get_any_thumbnail_if_exists(source: str, size: str = 'small') -> str:
    """ Get the path of a thumbnail stored inside either an atlas or the thumbnail cache """
    return get_atlas_thumbnail_if_exists(source, size) or get_thumbnail_if_exists(source)


def get_atlas_thumbnail_if_exists(source: str, size: str) -> str:
    """Get the path of a thumbnail stored inside an atlas, if available

    Args:
        source (str): File path or URI for image source

    Returns:
        str: `atlas://` path, if found; otherwise ``None``
    """
    return get_resource_path_if_exists(size, get_thumbnail_hash(source))


# TODO: Not quite working as intended
def async_image_to_monochrome(async_image, **kwargs):
    image_bytes, ext = async_image.get_image_bytes()
    image_bytes = to_monochrome(image_bytes, ext)
    image_bytes.seek(0)
    return Image(image_bytes, ext=ext)
