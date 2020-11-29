from itertools import chain
from logging import getLogger
from typing import Any, Dict, List

from naturtag.inat_metadata import quote, sort_taxonomy_keywords

# All tags that support regular and hierarchical keyword lists
KEYWORD_TAGS = [
    'Exif.Image.XPSubject',
    'Iptc.Application2.Subject',
    'Xmp.dc.subject',
]
HIER_KEYWORD_TAGS = [
    'Exif.Image.XPKeywords',
    'Iptc.Application2.Keywords',
    'Xmp.lr.hierarchicalSubject',
]

logger = getLogger().getChild(__name__)


class KeywordMetadata:
    """
    Container for combining, parsing, and organizing keyword metadata into relevant categories
    """

    def __init__(self, metadata=None, keywords=None):
        """ Initialize with full metadata or keywords only """
        self.keywords = keywords or self.get_combined_keywords(metadata)
        self.kv_keywords = self.get_kv_keywords()
        self.hier_keywords = self.get_hierarchical_keywords()
        self.normal_keywords = self.get_normal_keywords()

    def get_combined_keywords(self, metadata: Dict[str, Any]) -> List[str]:
        """ Get keywords from all metadata formats """
        if not metadata:
            return []

        # All keywords will be combined and re-sorted, to account for errors in other programs
        keywords = [
            self._get_keyword_list(metadata, tag) for tag in KEYWORD_TAGS + HIER_KEYWORD_TAGS
        ]
        keywords = set(chain.from_iterable(keywords))
        logger.info(f'{len(keywords)} unique keywords found')
        return [k.replace('"', '') for k in keywords]

    @staticmethod
    def _get_keyword_list(metadata: Dict[str, Any], tag: str) -> List[str]:
        """ Split comma-separated keywords into a list, if not already a list """
        keywords = metadata.get(tag, [])
        if isinstance(keywords, list):
            return keywords
        elif ',' in keywords:
            return [kw.strip() for kw in ','.split(keywords)]
        else:
            return [keywords.strip()] if keywords.strip() else []

    def get_kv_keywords(self) -> Dict[str, str]:
        """ Get all keywords that contain key-value pairs"""
        kv_keywords = [kw for kw in self.keywords if kw.count('=') == 1 and kw.split('=')[1]]
        kv_keywords = sort_taxonomy_keywords(kv_keywords)
        logger.info(f'{len(kv_keywords)} unique key-value pairs found in keywords')
        return dict([kw.split('=') for kw in kv_keywords])

    def get_hierarchical_keywords(self) -> List[str]:
        """
        Get all hierarchical keywords as flat strings.
        Also Account for root node (single value without '|')
        """
        hier_keywords = [kw for kw in self.keywords if '|' in kw]
        if hier_keywords:
            root = hier_keywords[0].split('|')[0]
            hier_keywords.insert(0, root)
        return hier_keywords

    def get_normal_keywords(self) -> List[str]:
        """ Get all single-value keywords that are neither a key-value pair nor hierarchical """
        return sorted([k for k in self.keywords if '=' not in k and '|' not in k])

    @property
    def flat_keywords(self) -> List[str]:
        """ Get all non-hierarchical keywords """
        return [kw for kw in self.keywords if '|' not in kw]

    @property
    def flickr_tags(self):
        """ Get all taxonomy and normal keywords as quoted, space-separated tags compatible with Flickr """
        return ' '.join([quote(kw) for kw in self.kv_keyword_list + self.normal_keywords])

    @property
    def hier_keyword_tree(self) -> Dict[str, Any]:
        """ Get all hierarchical keywords as a nested dict """
        kw_tree = {}
        for kw_ranks in [kw.split('|') for kw in self.hier_keywords]:
            kw_tree = self._append_nodes(kw_tree, kw_ranks)
        return kw_tree

    @staticmethod
    def _append_nodes(tree, kw_tokens):
        tree_node = tree
        for token in kw_tokens:
            tree_node = tree_node.setdefault(token, {})
        return tree

    @property
    def hier_keyword_tree_str(self) -> str:
        """ Get all hierarchical keywords as a single string, in indented tree format """
        return dict_to_indented_tree(self.hier_keyword_tree)

    @property
    def kv_keyword_list(self) -> List[str]:
        """ Join key-value pairs back into strings """
        return [f'{k}={v}' for k, v in self.kv_keywords.items()]

    @property
    def tags(self) -> Dict[str, Any]:
        """
        Add all keywords to all appropriate XMP, EXIF, and IPTC tags

        Returns:
            dict: Mapping from qualified tag name to tag value(s)
        """
        metadata = {tag: self.flat_keywords for tag in KEYWORD_TAGS}
        metadata.update({tag: self.hier_keywords for tag in HIER_KEYWORD_TAGS})
        return metadata


def dict_to_indented_tree(d: Dict[str, Any]) -> str:
    """ Convert a dict-formatted tree into a single string, in indented tree format """

    def append_children(d, indent_lvl):
        subtree = ''
        for k, v in d.items():
            subtree += ' ' * indent_lvl + k + '\n'
            subtree += append_children(v, indent_lvl + 1)
        return subtree

    return append_children(d, 0)
