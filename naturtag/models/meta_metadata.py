from logging import getLogger
from os.path import basename
from typing import Dict, List, Optional

from naturtag.constants import IntTuple, StrTuple
from naturtag.inat_metadata import get_inaturalist_ids, get_min_rank
from naturtag.models import HIER_KEYWORD_TAGS, KEYWORD_TAGS, ImageMetadata, KeywordMetadata

logger = getLogger().getChild(__name__)


# TODO: Extract GPS info
# TODO: __str__
class MetaMetadata(ImageMetadata):
    """ Class for parsing & organizing info derived from basic image metadata """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define lazy-loaded properties
        self._inaturalist_ids = None
        self._min_rank = None
        self._simplified = None
        self._summary = None
        self.combined = None
        self.keyword_meta = None
        self._update_derived_properties()

    def _update_derived_properties(self):
        """ Reset/ update all secondary properties derived from base metadata formats """
        self._inaturalist_ids = None
        self._min_rank = None
        self._simplified = None
        self._summary = None
        self.combined = {**self.exif, **self.iptc, **self.xmp}
        self.keyword_meta = KeywordMetadata(self.combined)

    @property
    def inaturalist_ids(self) -> IntTuple:
        """ Get taxon and/or observation IDs from metadata if available """
        if self._inaturalist_ids is None:
            self._inaturalist_ids = get_inaturalist_ids(self.simplified)
        return self._inaturalist_ids

    @property
    def taxon_id(self) -> Optional[int]:
        return self.inaturalist_ids[0]

    @property
    def observation_id(self) -> Optional[int]:
        return self.inaturalist_ids[1]

    @property
    def min_rank(self) -> StrTuple:
        """ Get the lowest (most specific) taxonomic rank from tags, if any """
        if self._min_rank is None:
            self._min_rank = get_min_rank(self.simplified)
        return self._min_rank

    @property
    def has_taxon(self) -> bool:
        return bool(self.taxon_id or all(self.min_rank))

    @property
    def simplified(self) -> Dict[str, str]:
        """
        Get simplified/deduplicated key-value pairs from a combination of keywords + basic metadata
        """
        if self._simplified is None:
            self._simplified = simplify_keys({**self.combined, **self.keyword_meta.kv_keywords})
            for k in KEYWORD_TAGS + HIER_KEYWORD_TAGS:
                self._simplified.pop(k, None)
        return self._simplified

    @property
    def summary(self) -> str:
        """ Get a condensed summary of available metadata """
        if self._summary is None:
            meta_types = {
                'EXIF': bool(self.exif),
                'IPTC': bool(self.iptc),
                'XMP': bool(self.xmp),
                'SIDECAR': self.has_sidecar,
            }
            meta_special = {
                'TAX': self.has_taxon,
                'OBS': self.observation_id,
                # 'GPS': self.gps,
            }
            logger.info(f'Metadata summary: {meta_types} {meta_special}')

            self._summary = '\n'.join(
                [
                    basename(self.image_path),
                    ' | '.join([k for k, v in meta_special.items() if v]),
                    ' | '.join([k for k, v in meta_types.items() if v]),
                ]
            )
        return self._summary

    def update(self, new_metadata):
        """ Update arbitrary EXIF, IPTC, and/or XMP metadata, and reset/update derived properties """
        super().update(new_metadata)
        self._update_derived_properties()

    def update_keywords(self, keywords):
        """
        Update only keyword metadata.
        Keywords will be written to appropriate tags for each metadata format.
        """
        self.update(KeywordMetadata(keywords=keywords).tags)


def get_tagged_image_metadata(paths: List[str]) -> Dict[str, MetaMetadata]:
    all_image_metadata = (MetaMetadata(path) for path in paths)
    return {m.image_path: m for m in all_image_metadata if m.taxon_id or m.observation_id}


def simplify_keys(mapping: Dict[str, str]) -> Dict[str, str]:
    """
    Simplify/deduplicate dict keys, to reduce variations in similarly-named keys

    Example::
        >>> simplify_keys({'my_namepace:Super_Order': 'Panorpida'})
        {'superfamily': 'Panorpida'}

    Returns:
        Dict with simplified/deduplicated keys
    """
    return {k.lower().replace('_', '').split(':')[-1]: v for k, v in mapping.items()}
