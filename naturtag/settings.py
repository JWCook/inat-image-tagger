""" Basic utilities for reading and writing settings from config files """
import json
from collections import Counter, OrderedDict
from logging import getLogger
from os import makedirs
from os.path import isfile
from shutil import copyfile
from typing import Any, Dict

import yaml

from naturtag.constants import CONFIG_PATH, DATA_DIR, DEFAULT_CONFIG_PATH, STORED_TAXA_PATH
from naturtag.validation import convert_int_dict

logger = getLogger().getChild(__name__)


def read_settings() -> Dict[str, Any]:
    """Read settings from the settings file

    Returns:
        Stored config state
    """
    if not isfile(CONFIG_PATH):
        reset_defaults()
    logger.info(f'Settings: Reading settings from {CONFIG_PATH}')
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def write_settings(new_config: Dict[str, Any]):
    """Write updated settings to the settings file

    Args:
        new_config (dict): Updated config state
    """
    # First re-read current config, in case it changed on disk (manual edits)
    # And update on a per-section basis so we don't overwrite with an empty section
    settings = read_settings()
    logger.info(f'Settings: Writing settings to {CONFIG_PATH}')
    for k, v in new_config.items():
        logger.debug(f'Settings: Writing {k}={v}')
        settings.setdefault(k, {})
        settings[k].update(v)
    logger.info('Settings: Done')

    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(settings, f)


def reset_defaults():
    """ Reset settings to defaults """
    logger.info(f'Settings: Resetting {CONFIG_PATH} to defaults')
    makedirs(DATA_DIR, exist_ok=True)
    copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)


# TODO: Separately store loaded history, new history for session; only write (append) new history
def read_stored_taxa() -> Dict:
    """Read taxon view history, starred, and frequency

    Returns:
        Stored taxon view history, starred, and frequency
    """
    if not isfile(STORED_TAXA_PATH):
        stored_taxa = {}
    else:
        with open(STORED_TAXA_PATH) as f:
            stored_taxa = json.load(f)

    stored_taxa.setdefault('history', [])
    stored_taxa.setdefault('starred', [])
    stored_taxa['frequent'] = convert_int_dict(stored_taxa.get('frequent', {}))
    stored_taxa['observed'] = convert_int_dict(stored_taxa.get('observed', {}))
    return stored_taxa


def write_stored_taxa(stored_taxa: Dict):
    """Write taxon view history to file, along with stats on most frequently viewed taxa

    Args:
        Complete taxon history (including previously stored history)
    """
    # Do a recount/resort before writing
    stored_taxa["frequent"] = OrderedDict(Counter(stored_taxa["history"]).most_common())

    logger.info(
        'Settings: Writing stored taxa: '
        f'{len(stored_taxa["history"])} history items, '
        f'{len(stored_taxa["starred"])} starred items, '
        f'{len(stored_taxa["frequent"])} frequent items, '
        f'{len(stored_taxa["observed"])} observed items'
    )
    with open(STORED_TAXA_PATH, 'w') as f:
        json.dump(stored_taxa, f, indent=4)
    logger.info('Settings: Done')
