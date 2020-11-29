""" Utilities for generating and retrieving image thumbnails """
from hashlib import md5
from io import BytesIO, IOBase
from logging import getLogger
from os import makedirs, scandir
from os.path import dirname, getsize, isfile, join, normpath, splitext
from shutil import copyfileobj, rmtree
from typing import BinaryIO, Optional, Tuple, Union

import requests
from PIL import Image
from PIL.ImageOps import exif_transpose, flip

from naturtag.constants import (
    EXIF_ORIENTATION_ID,
    THUMBNAIL_DEFAULT_FORMAT,
    THUMBNAIL_SIZE_DEFAULT,
    THUMBNAIL_SIZES,
    THUMBNAILS_DIR,
)
from naturtag.validation import format_file_size

logger = getLogger().getChild(__name__)


def get_thumbnail(source: str, **kwargs) -> str:
    """
    Get a cached thumbnail for an image, if one already exists; otherwise, generate a new one.
    See :py:func:`.generate_thumbnail` for size options.

    Args:
        source: File path or URI for image source

    Returns:
        Path to thumbnail image
    """
    thumbnail_path = get_thumbnail_path(source)
    if isfile(thumbnail_path):
        return thumbnail_path
    else:
        return generate_thumbnail(source, thumbnail_path, **kwargs)


def get_thumbnail_if_exists(source: str) -> Optional[str]:
    """
    Get a cached thumbnail for an image, if one already exists, but if not, don't generate a new one

    Args:
        source: File path or URI for image source

    Returns:
        The path of the new thumbnail, if found; otherwise ``None``
    """
    if not source:
        return None

    thumbnail_path = get_thumbnail_path(source)
    if isfile(thumbnail_path):
        logger.debug(f'Found existing thumbnail for {source}')
        return thumbnail_path
    elif normpath(dirname(source)) == normpath(THUMBNAILS_DIR) or source.startswith('atlas://'):
        logger.debug(f'Image is already a thumbnail: {source}')
        return source
    else:
        return None


def get_thumbnail_hash(source: str) -> str:
    """ Get a unique string based on the source to use as a filename or atlas resource ID """
    if not isinstance(source, bytes):
        source = source.encode()
    return md5(source).hexdigest()


def get_thumbnail_size(size: str) -> Tuple[int, int]:
    """Get one of the predefined thumbnail dimensions from a size string

    Args:
        size: One of: 'small', 'medium', 'large'

    Returns:
        X and Y dimensions of thumbnail size
    """
    return THUMBNAIL_SIZES.get(size, THUMBNAIL_SIZE_DEFAULT)


def get_thumbnail_path(source: str) -> str:
    """
    Determine the thumbnail filename based on a hash of the original file path

    Args:
        source: File path or URI for image source
    """
    makedirs(THUMBNAILS_DIR, exist_ok=True)
    thumbnail_hash = get_thumbnail_hash(source)
    ext = get_format(source)
    return join(THUMBNAILS_DIR, f'{thumbnail_hash}.{ext}')


def get_format(source: str) -> str:
    """
    Account for various edge cases when getting an image format based on a file extension

    Args:
        source: File path or URI for image source

    Returns:
        Format, if found; otherwise, defaults to ``jpg``
    """
    if isinstance(source, bytes):
        source = source.decode('utf-8')
    # Strip off request params if path is a URL
    source = source.split('?')[0]
    ext = splitext(source)[-1] or THUMBNAIL_DEFAULT_FORMAT
    # Note: PIL only accepts 'jpeg' (not 'jpg'), and Kivy is the opposite
    return ext.lower().replace('.', '').replace('jpeg', 'jpg') or 'jpg'


def generate_thumbnail_from_url(url: str, size: str):
    """ Like :py:func:`.generate_thumbnail`, but downloads an image from a URL """
    logger.info(f'Downloading: {url}')
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        image_bytes = BytesIO()
        r.raw.decode_content = True
        copyfileobj(r.raw, image_bytes)
        generate_thumbnail_from_bytes(image_bytes, url, size=size, default_flip=False)
    else:
        logger.info(f'Request failed: {str(r)}')


def generate_thumbnail_from_bytes(image_bytes, source: str, **kwargs):
    """ Like :py:func:`.generate_thumbnail`, but takes raw image bytes instead of a path """
    image_bytes.seek(0)
    fmt = get_format(source)
    thumbnail_path = get_thumbnail_path(source)

    if len(image_bytes.getvalue()) > 0:
        return generate_thumbnail(image_bytes, thumbnail_path, fmt=fmt, **kwargs)
    else:
        logger.error(f'Failed to save image bytes to thumbnail for {source}')
        return None


def generate_thumbnail(
    source: Union[BinaryIO, str],
    thumbnail_path: str,
    fmt: str = None,
    size: str = 'medium',
    default_flip: bool = True,
):
    """
    Generate and store a thumbnail from the source image

    Args:
        source (str): File path or URI for image source
        thumbnail_path (str): Destination path for thumbnail
        fmt (str): Image format to specify to PIL, if it can't be auto-detected
        size (str): One of: 'small', 'medium', 'large'

    Returns:
        str: The path of the new thumbnail
    """
    target_size = get_thumbnail_size(size)
    logger.info(f'Generating {target_size} thumbnail for {source}:\n  {thumbnail_path}')

    # Resize if necessary, or just copy the image to the cache if it's already thumbnail size
    try:
        image = get_orientated_image(source, default_flip=default_flip)
        if image.size[0] > target_size[0] or image.size[1] > target_size[1]:
            image.thumbnail(target_size)
        else:
            logger.debug(f'Image is already thumbnail size: ({image.size})')
        image.save(thumbnail_path, format=fmt.replace('jpg', 'jpeg') if fmt else None)
        return thumbnail_path

    # If we're unable to generate a thumbnail, just return the original image source
    except RuntimeError:
        logger.exception('Failed to generate thumbnail')
        return source


def get_orientated_image(source, default_flip: bool = True) -> Image:
    """
    Load and rotate/transpose image according to EXIF orientation, if any. If missing orientation
    and the image was fetched from iNat, it will be vertically mirrored. (?)
    """
    image = Image.open(source)
    exif = image.getexif()

    if exif.get(EXIF_ORIENTATION_ID):
        image = exif_transpose(image)
    # TODO: In the future there may be more cases than just local images and remote images from iNat
    elif default_flip and isinstance(source, IOBase):
        image = flip(image)

    return image


def get_thumbnail_cache_size() -> Tuple[int, str]:
    """Get the current size of the thumbnail cache, in number of files and human-readable
    total file size
    """
    files = [f for f in scandir(THUMBNAILS_DIR) if isfile(f)]
    file_size = sum(getsize(f) for f in files)
    return len(files), format_file_size(file_size)


def delete_thumbnails():
    """Delete call cached thumbnails"""
    rmtree(THUMBNAILS_DIR)
    makedirs(THUMBNAILS_DIR)


def flip_all(path: str):
    """Vertically flip all images in a directory. Mainly for debugging purposes."""
    from naturtag.image_glob import get_images_from_dir

    for source in get_images_from_dir(path):
        image = Image.open(source)
        image = flip(image)
        image.save(source)
        image.close()


def to_monochrome(source, fmt):
    """Convert an image to monochrome"""
    img = Image.open(source)
    img.convert(mode='1')
    img.save(source, format=fmt.replace('jpg', 'jpeg') if fmt else None)
    return source
