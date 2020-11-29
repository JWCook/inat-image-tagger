""" Data classes with utilities for managing specific resources """
# flake8: noqa: F401
# TODO: simplified __str__ implementations
from contextlib import contextmanager


@contextmanager
def suppress_version_error():
    """Suppress pyexiv2 version check; it seems that it works on python 3.9
    but error hasn't been updated
    """
    import platform

    original_python_version = platform.python_version
    platform.python_version = lambda: '3.8'
    yield
    platform.python_version = original_python_version


# Imported in order of dependencies
from naturtag.models.base import BaseModel, aliased_kwarg, kwarg, timestamp
from naturtag.models.photo import Photo
from naturtag.models.taxon import Taxon, get_icon_path
from naturtag.models.user import User
from naturtag.models.identification import Identification
from naturtag.models.observation import Observation
from naturtag.models.image_metadata import ImageMetadata
from naturtag.models.keyword_metadata import KeywordMetadata, KEYWORD_TAGS, HIER_KEYWORD_TAGS
from naturtag.models.meta_metadata import MetaMetadata
