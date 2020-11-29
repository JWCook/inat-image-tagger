from collections import OrderedDict
from os.path import dirname, join
from typing import Optional, Tuple

from appdirs import user_data_dir
from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.request_params import CC_LICENSES, RANKS  # noqa: F401

from naturtag import __version__

# Resource directories
PKG_DIR = dirname(dirname(__file__))
ASSETS_DIR = join(PKG_DIR, 'assets', '')
KV_SRC_DIR = join(PKG_DIR, 'kv')
ICONS_DIR = join(ASSETS_DIR, 'iconic_taxa')
DATA_DIR = join(user_data_dir(), 'Naturtag')

# TODO: These may be useful as user-configurable settings
TRIGGER_DELAY = 0.1
AUTOCOMPLETE_DELAY = 0.5
AUTOCOMPLETE_MIN_CHARS = 3
IMAGE_FILETYPES = ['*.jpg', '*.jpeg', '*.png', '*.gif']
PHOTO_SIZES = ['square', 'small', 'medium', 'large', 'original']

# Thumnbnail & cache settings
EXIF_ORIENTATION_ID = '0x0112'
THUMBNAILS_DIR = join(DATA_DIR, 'thumbnails')
THUMBNAIL_DEFAULT_FORMAT = 'png'
THUMBNAIL_SIZE_SM = (75, 75)
THUMBNAIL_SIZE_DEFAULT = (200, 200)
THUMBNAIL_SIZE_LG = (500, 500)
THUMBNAIL_SIZES = {
    'small': THUMBNAIL_SIZE_SM,
    'medium': THUMBNAIL_SIZE_DEFAULT,
    'large': THUMBNAIL_SIZE_LG,
}

# Atlas settings
ATLAS_MAX_SIZE = 4096
ATLAS_BASE = 'atlas://../../assets/atlas'  # Path is relative to Kivy app.py
ATLAS_PATH = join(ASSETS_DIR, 'atlas', 'taxon_icons.atlas')
ATLAS_TAXON_ICONS = f'{ATLAS_BASE}/taxon_icons'
ATLAS_TAXON_PHOTOS = f'{ATLAS_BASE}/taxon_photos'
ATLAS_LOCAL_PHOTOS = f'{ATLAS_BASE}/local_photos'
ATLAS_APP_ICONS = f'{ATLAS_BASE}/app_icons'
ALL_ATLASES = [ATLAS_APP_ICONS, ATLAS_TAXON_ICONS, ATLAS_TAXON_PHOTOS, ATLAS_LOCAL_PHOTOS]

# Cache settings
CACHE_PATH = join(DATA_DIR, 'inaturalist_api_cache')
API_CACHE_EXPIRY_HOURS = 0
OBS_CACHE_EXPIRY_HOURS = 48
CACHE_BACKEND = 'sqlite'

# Config files
CONFIG_PATH = join(DATA_DIR, 'settings.yml')
DEFAULT_CONFIG_PATH = join(PKG_DIR, 'default_settings.yml')
STORED_TAXA_PATH = join(DATA_DIR, 'stored_taxa.json')
MAX_DISPLAY_HISTORY = 50  # Max number of history items to display at a time

# URLs / API settings
OBSERVATION_BASE_URL = 'https://www.inaturalist.org/observations'
PHOTO_BASE_URL = 'https://static.inaturalist.org/photos'
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'
PLACES_BASE_URL = 'https://www.inaturalist.org/places'
TAXON_BASE_URL = 'https://www.inaturalist.org/taxa'
USER_AGENT = f'naturtag/{__version__}; {DEFAULT_USER_AGENT}'.lower()

# Theme/window settings
INIT_WINDOW_POSITION = ('custom', 100, 100)
INIT_WINDOW_SIZE = (1500, 900)
MD_PRIMARY_PALETTE = 'Teal'
MD_ACCENT_PALETTE = 'Cyan'
MAX_LABEL_CHARS = 80

# Key codes; reference: https://gist.github.com/Enteleform/a2e4daf9c302518bf31fcc2b35da4661
BACKSPACE = 8
ENTER = 13
F11 = 292

# Simplified tags without formatting variations
TAXON_KEYS = ['taxonid', 'dwc:taxonid']
OBSERVATION_KEYS = ['observationid', 'catalognumber', 'dwc:catalognumber']

# Iconic taxa, aka common taxon search categories, in the same order as shown on the iNar web UI
ICONIC_TAXA = OrderedDict(
    [
        (3, 'aves'),
        (20978, 'amphibia'),
        (26036, 'reptilia'),
        (40151, 'mammalia'),
        (47178, 'actinopterygii'),
        (47115, 'mollusca'),
        (47119, 'arachnida'),
        (47158, 'insecta'),
        (47126, 'plantae'),
        (47170, 'fungi'),
        (48222, 'chromista'),
        (47686, 'protozoa'),
    ]
)
# Other not-quite-as-iconic icons to show
ICONISH_TAXA = {**ICONIC_TAXA, 1: 'animalia', 0: 'unknown'}
PLACEHOLDER_ICON = f'{ATLAS_APP_ICONS}/unknown'

# Specific XML namespaces to use terms from when processing DwC observation records
# Note: exiv2 will automatically add recognized namespaces when adding properties
DWC_NAMESPACES = {
    "dcterms": "http://purl.org/dc/terms/",
    "dwc": "http://rs.tdwg.org/dwc/terms/",
}

# Basic DwC fields that can be added for a taxon without an observation
MINIMAL_DWC_TERMS = [
    'dwc:kingdom',
    'dwc:phylum',
    'dwc:class',
    'dwc:order',
    'dwc:family',
    'dwc:genus',
    'dwc:species',
    'dwc:scientificName',
    'dwc:taxonRank',
    'dwc:taxonID',
]

COMMON_NAME_IGNORE_TERMS = [
    ',',
    ' and ',
    'allies',
    'relatives',
]

# Type aliases
IntTuple = Tuple[Optional[int], Optional[int]]
StrTuple = Tuple[Optional[str], Optional[str]]
Coordinates = Optional[Tuple[float, float]]
