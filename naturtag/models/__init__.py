""" Data classes with utilities for managing specific resources """
# flake8: noqa: F401
# TODO: simplified __str__ implementations

# Imported in order of dependencies
from naturtag.models.base import BaseModel, aliased_kwarg, kwarg, timestamp
from naturtag.models.identification import Identification
from naturtag.models.image_metadata import ImageMetadata
from naturtag.models.keyword_metadata import HIER_KEYWORD_TAGS, KEYWORD_TAGS, KeywordMetadata
from naturtag.models.meta_metadata import MetaMetadata
from naturtag.models.observation import Observation
from naturtag.models.photo import Photo
from naturtag.models.taxon import Taxon, get_icon_path
from naturtag.models.user import User
