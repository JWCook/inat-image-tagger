import attr
from typing import List, Dict, Optional

from pyinaturalist.node_api import get_taxa_by_id
from naturtag.inat_metadata import get_rank_idx
from naturtag.constants import TAXON_BASE_URL, ICONISH_TAXA, ATLAS_APP_ICONS, CC_LICENSES

kwarg = attr.ib(default=None)


@attr.s
class Taxon:
    """A data class containing information about a taxon, matching the schema of ``GET /taxa``
    from the iNaturalist API: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    Examples of partial records include nested ``ancestors``, ``children``, and results from
    :py:func:`get_taxa_autocomplete`
    """

    id: int = kwarg
    partial: bool = kwarg

    ancestry: str = kwarg
    atlas_id: int = kwarg
    complete_rank: str = kwarg
    complete_species_count: int = kwarg
    extinct: bool = kwarg
    iconic_taxon_id: int = kwarg
    iconic_taxon_name: str = kwarg
    is_active: bool = kwarg
    listed_taxa_count: int = kwarg
    name: str = kwarg
    observations_count: int = kwarg
    parent_id: int = kwarg
    rank: str = kwarg
    rank_level: int = kwarg
    taxon_changes_count: int = kwarg
    taxon_schemes_count: int = kwarg
    wikipedia_summary: str = kwarg
    wikipedia_url: str = kwarg
    preferred_common_name: str = attr.ib(default='')

    # Nested collections with defaults
    ancestor_ids: List[int] = attr.ib(factory=list)
    ancestors: List[Dict] = attr.ib(factory=list)
    children: List[Dict] = attr.ib(factory=list)
    conservation_statuses: List[str] = attr.ib(factory=list)
    current_synonymous_taxon_ids: List[int] = attr.ib(factory=list)
    default_photo: Dict = attr.ib(factory=dict)
    flag_counts: Dict = attr.ib(factory=dict)
    listed_taxa: List = attr.ib(factory=list)
    taxon_photos: List = attr.ib(factory=list)

    # Internal attrs managed by @properties
    _parent_taxa: List = attr.ib(default=None)
    _child_taxa: List = attr.ib(default=None)

    @classmethod
    def from_id(cls, id: int):
        """ Lookup and create a new Taxon object from an ID """
        r = get_taxa_by_id(id)
        json = r['results'][0]
        return cls.from_dict(json)

    @classmethod
    def from_dict(cls, json: Dict, partial: bool = False):
        """ Create a new Taxon object from all or part of an API response """
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(partial=partial, **valid_json)

    # TODO: Seems like there should be a better way to do this.
    def update_from_full_record(self):
        t = Taxon.from_id(self.id)
        self.ancestors = t.ancestors
        self.children = t.children
        self.default_photo = t.default_photo
        self.taxon_photos = t.taxon_photos

    @property
    def ancestry_str(self):
        return ' | '.join(t.name for t in self.parent_taxa)

    @property
    def icon_path(self) -> str:
        return get_icon_path(self.iconic_taxon_id)

    @property
    def link(self) -> str:
        return f'{TAXON_BASE_URL}/{self.id}'

    @property
    def photo_url(self) -> str:
        return self.default_photo.get('medium_url')

    @property
    def has_cc_photo(self) -> bool:
        """ Determine if there is a default photo with a Creative Commons license """
        license = self.default_photo.get('license_code', '').upper()
        return license in CC_LICENSES and self.photo_url

    @property
    def thumbnail_url(self) -> str:
        return self.default_photo.get('square_url')

    @property
    def parent_taxa(self) -> List:
        """ Get this taxon's ancestors as Taxon objects (in descending order of rank) """
        if self._parent_taxa is None:
            if not self.ancestors:
                self.update_from_full_record()
            self._parent_taxa = [Taxon.from_dict(t, partial=True) for t in self.ancestors]
        return self._parent_taxa

    @property
    def parent_taxa_ids(self) -> List:
        return [taxon.id for taxon in self.parent_taxa]

    @property
    def parent(self):
        """ Return immediate parent, if any """
        return self.parent_taxa[-1] if self.parent_taxa else None

    @property
    def child_taxa(self) -> List:
        """ Get this taxon's children as Taxon objects (in descending order of rank) """

        def get_child_idx(taxon):
            return get_rank_idx(taxon.rank), taxon.name

        if self._child_taxa is None:
            # TODO: Determine if it's already a full record but the taxon has no children?
            if not self.children:
                self.update_from_full_record()
            self._child_taxa = [Taxon.from_dict(t, partial=True) for t in self.children]
            # Children may be different ranks; sort children by rank then name
            self._child_taxa.sort(key=get_child_idx)
        return self._child_taxa

    @property
    def child_taxa_ids(self) -> List:
        return [taxon.id for taxon in self.child_taxa]


def get_icon_path(id: int) -> Optional[str]:
    """ An iconic function to return an icon for an iconic taxon """
    if id not in ICONISH_TAXA:
        id = 0
    return f'{ATLAS_APP_ICONS}/{ICONISH_TAXA[id]}'
