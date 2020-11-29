""" Tools to get keyword tags (e.g., for XMP metadata) from iNaturalist observations """
from datetime import timedelta
from logging import getLogger
from os import makedirs
from os.path import dirname, getsize
from typing import Dict, List, Optional, Tuple

import requests_cache
import xmltodict
from pyinaturalist.node_api import (
    get_observation,
    get_observation_species_counts,
    get_taxa,
    get_taxa_by_id,
)
from pyinaturalist.rest_api import get_observations

from naturtag.constants import (
    API_CACHE_EXPIRY_HOURS,
    CACHE_BACKEND,
    CACHE_PATH,
    COMMON_NAME_IGNORE_TERMS,
    DWC_NAMESPACES,
    OBSERVATION_KEYS,
    RANKS,
    TAXON_KEYS,
    IntTuple,
    StrTuple,
)
from naturtag.validation import format_file_size

# Patch requests to use CachedSession for pyinaturalist API calls
makedirs(dirname(CACHE_PATH), exist_ok=True)
requests_cache.install_cache(
    backend=CACHE_BACKEND,
    cache_name=CACHE_PATH,
    expire_after=timedelta(hours=API_CACHE_EXPIRY_HOURS),
)
logger = getLogger().getChild(__name__)


def get_http_cache_size() -> str:
    """Get the current size of the HTTP request cache, in human-readable format"""
    return format_file_size(getsize(f'{CACHE_PATH}.{CACHE_BACKEND}'))


def get_observation_taxon(observation_id: int) -> int:
    """ Get the current taxon ID for the given observation """
    logger.info(f'API: Fetching observation {observation_id}')
    obs = get_observation(observation_id)
    if obs.get('community_tax_id') and obs['community_tax_id'] != obs['taxon']['id']:
        logger.warning('API: Community ID does not match selected taxon')
    return obs['taxon']['id']


def get_observation_dwc_terms(observation_id: int) -> Dict[str, str]:
    """ Get all DWC terms from an iNaturalist observation """
    logger.info(f'API: Getting Darwin Core terms for observation {observation_id}')
    obs_dwc = get_observations(id=observation_id, response_format='dwc')
    return convert_dwc_to_xmp(obs_dwc)


# TODO: separate species, binomial, trinomial
def get_keywords(
    observation_id: int = None,
    taxon_id: int = None,
    common: bool = False,
    hierarchical: bool = False,
) -> List[str]:
    """ Get all taxonomic keywords for a given observation or taxon """
    min_tax_id = taxon_id or get_observation_taxon(observation_id)
    taxa = get_taxon_with_ancestors(min_tax_id)

    keywords = get_taxonomy_keywords(taxa)
    if hierarchical:
        keywords.extend(get_hierarchical_keywords(keywords))
    if common:
        keywords.extend(get_common_keywords(taxa))

    keywords.append(f'inat:taxon_id={min_tax_id}')
    keywords.append(f'dwc:taxonID={min_tax_id}')
    if observation_id:
        keywords.append(f'inat:observation_id={observation_id}')
        keywords.append(f'dwc:catalogNumber={observation_id}')

    logger.info(f'API: {len(keywords)} total keywords generated')
    return keywords


def get_taxon_children(taxon_id: int) -> List[Dict]:
    """ Get a taxon's children """
    logger.info(f'API: Fetching children of taxon {taxon_id}')
    r = get_taxa(parent_id=taxon_id)
    logger.info(f'API: {len(r["results"])} child taxa found')
    return r['results']


def get_taxon_ancestors(taxon_id: int) -> List[Dict]:
    """ Get a taxon's parents """
    return get_taxon_with_ancestors(taxon_id)[:-1]


def get_taxon_with_ancestors(taxon_id: int) -> List[Dict]:
    """ Get a taxon with all its parents """
    logger.info(f'API: Fetching parents of taxon {taxon_id}')
    r = get_taxa_by_id(taxon_id)
    taxon = r['results'][0]
    logger.info(f'API: {len(taxon["ancestors"])} parent taxa found')
    return taxon['ancestors'] + [taxon]


# TODO: This should be reorganized somehow, I don't quite like the look if it;
#  image_metadata module depends on this module and vice versa (kinda)
def get_taxon_and_obs_from_metadata(metadata) -> Tuple[Dict, Dict]:
    logger.info(f'API: Searching for matching taxon and/or observation for {metadata.image_path}')
    taxon, observation = get_observation_from_metadata(metadata)
    if not taxon and metadata.has_taxon:
        taxon = get_taxon_from_metadata(metadata)
    if not taxon:
        logger.info('API: No taxon found')
    return taxon, observation


def get_observation_from_metadata(metadata) -> Tuple[Dict, Dict]:
    if not metadata.observation_id:
        logger.info('API: No observation ID specified')
        return None, None

    observation = get_observation(metadata.observation_id)
    taxon = None
    taxon_id = observation.get('taxon', {}).get('id')

    # Handle observation with no taxon ID (e.g., not yet identified)
    if taxon_id:
        taxon = get_taxa_by_id(taxon_id).get('results', [None])[0]
        logger.info(f'API: Found observation {metadata.observation_id} and taxon {taxon_id}')
    else:
        logger.warning(f'API: Observation {metadata.observation_id} is unidentified')

    return taxon, observation


def get_taxon_from_metadata(metadata) -> Optional[Dict]:
    """ Fetch taxon record from MetaMetadata object: either by ID or rank + name """
    rank, name = metadata.min_rank
    params = {'id': metadata.taxon_id} if metadata.taxon_id else {'rank': rank, 'q': name}
    logger.info(f'API: Querying taxon by: {params}')
    results = get_taxa(**params)['results']
    if results:
        logger.info('API: Taxon found')
        return results[0]
    else:
        return None


def get_taxonomy_keywords(taxa: List[Dict]) -> List[str]:
    """ Format a list of taxa into rank keywords """
    return [quote(f'taxonomy:{t["rank"]}={t["name"]}') for t in taxa]


def get_common_keywords(taxa: List[Dict]) -> List[str]:
    """Format a list of taxa into common name keywords.
    Filters out terms that aren't useful to keep as tags
    """
    keywords = [t.get('preferred_common_name', '') for t in taxa]

    def is_ignored(kw):
        return any([ignore_term in kw.lower() for ignore_term in COMMON_NAME_IGNORE_TERMS])

    common_keywords = [quote(kw) for kw in keywords if kw and not is_ignored(kw)]
    logger.info(
        f'API: {len(keywords) - len(common_keywords)} out of {len(keywords)} common names ignored'
    )
    return common_keywords


def get_observed_taxa(username: str, include_casual: bool = False) -> Dict[int, int]:
    """Get counts of taxa observed by the user, ordered by number of observations descending"""
    if not username:
        return {}
    logger.info(f'API: Searching for user-observed taxa (casual: {include_casual})')
    response = get_observation_species_counts(
        user_login=username,
        verifiable=None if include_casual else True,  # False will return *only* casual observations
    )
    logger.info(f'API: {len(response["results"])} user-observed taxa found')
    observed_taxa = {r['taxon']['id']: r['count'] for r in response['results']}
    return dict(sorted(observed_taxa.items(), key=lambda x: x[1], reverse=True))


# TODO: Also include common names in hierarchy?
def get_hierarchical_keywords(keywords: List) -> List[str]:
    hier_keywords = [keywords[0]]
    for rank_name in keywords[1:]:
        hier_keywords.append(f'{hier_keywords[-1]}|{rank_name}')
    return hier_keywords


def sort_taxonomy_keywords(keywords: List[str]) -> List[str]:
    """Sort keywords by taxonomic rank, where applicable"""

    def _get_rank_idx(tag):
        return get_rank_idx(tag.split(':')[-1].split('=')[0])

    return sorted(keywords, key=_get_rank_idx, reverse=True)


def get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0


def get_inaturalist_ids(metadata):
    """ Look for taxon and/or observation IDs from metadata if available """
    # Get first non-None value from specified keys, if any; otherwise return None
    def _first_match(d, keys):
        id = next(filter(None, map(d.get, keys)), None)
        return int(id) if id else None

    # Check all possible keys for valid taxon and observation IDs
    taxon_id = _first_match(metadata, TAXON_KEYS)
    observation_id = _first_match(metadata, OBSERVATION_KEYS)
    logger.info(f'API: Taxon ID: {taxon_id} | Observation ID: {observation_id}')
    return taxon_id, observation_id


def get_min_rank(metadata: Dict[str, str]) -> StrTuple:
    """ Get the lowest (most specific) taxonomic rank from tags, if any """
    for rank in RANKS:
        if rank in metadata:
            logger.info(f'API: Found minimum rank: {rank} = {metadata[rank]}')
            return rank, metadata[rank]
    return None, None


def quote(s: str) -> str:
    """ Surround keyword in quotes if it contains whitespace """
    return f'"{s}"' if ' ' in s else s


def convert_dwc_to_xmp(dwc: str) -> Dict[str, str]:
    """
    Get all DWC terms from XML content containing a SimpleDarwinRecordSet, and format them as
    XMP tags. For example: ``'dwc:species' -> 'Xmp.dwc.species'``
    """
    # Get inner record as a dict, if it exists
    xml_dict = xmltodict.parse(dwc)
    dwr = xml_dict.get('dwr:SimpleDarwinRecordSet', {}).get('dwr:SimpleDarwinRecord')
    if not dwr:
        logger.warning('API: No SimpleDarwinRecord found')
        return {}

    # iNat sometimes includes duplicate occurrence IDs
    if isinstance(dwr['dwc:occurrenceID'], list):
        dwr['dwc:occurrenceID'] = dwr['dwc:occurrenceID'][0]

    def _format_term(k):
        ns, term = k.split(':')
        return f'Xmp.{ns}.{term}'

    def _include_term(k):
        ns = k.split(':')[0]
        return ns in DWC_NAMESPACES

    # Format as XMP tags
    return {_format_term(k): v for k, v in dwr.items() if _include_term(k)}


def get_ids_from_url(value: str) -> IntTuple:
    """If a URL is provided containing an ID, return the taxon and/or observation ID.
    If it's an observation, fetch its taxon ID as well.

    Returns:
        taxon_id, observation_id
    """
    taxon_id, observation_id = None, None
    id = strip_url(value)
    # TODO: Update after finishing Observation model
    if 'observation' in value:
        observation_id = id
        json = get_observation(id)
        taxon_id = json.get('taxon', {}).get('id')
    elif 'taxa' in value:
        taxon_id = id

    return taxon_id, observation_id


def strip_url(value: str) -> Optional[int]:
    """ If a URL is provided containing an ID, return just the ID """
    try:
        return int(value.split('/')[-1].split('-')[0]) if value else None
    except (TypeError, ValueError):
        return None
