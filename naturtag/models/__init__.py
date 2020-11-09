""" Data classes with utilities for managing specific resources """
# TODO: base model

# Imported in order of dependencies
from naturtag.models.photo import Photo
from naturtag.models.taxon import Taxon, get_icon_path
from naturtag.models.user import User
from naturtag.models.identification import Identification
from naturtag.models.observation import Observation
from naturtag.models.image_metadata import ImageMetadata
from naturtag.models.keyword_metadata import KeywordMetadata, KEYWORD_TAGS, HIER_KEYWORD_TAGS
from naturtag.models.meta_metadata import MetaMetadata
