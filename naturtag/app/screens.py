""" Screen classes used by the app """
from logging import getLogger
from os.path import join
from typing import Any, Dict

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.screen import MDScreen

from naturtag.constants import KV_SRC_DIR

HOME_SCREEN = 'image_selection'
# TODO: Load kv files in corresponding widget modules instead?
SCREEN_COMPONENTS = [
    'widgets',
    'main',
    # 'autocomplete',
    'menus',
    'taxon_search',
    'taxon_selection',
]

logger = getLogger().getChild(__name__)


class Root(BoxLayout):
    pass


class CacheScreen(MDScreen):
    pass


class ImageSelectionScreen(MDScreen):
    pass


class SettingsScreen(MDScreen):
    pass


class MetadataViewScreen(MDScreen):
    pass


class TaxonScreen(MDScreen):
    pass


class ObservationScreen(MDScreen):
    pass


SCREENS = {
    HOME_SCREEN: ImageSelectionScreen,
    'cache': CacheScreen,
    'settings': SettingsScreen,
    'metadata': MetadataViewScreen,
    'taxon': TaxonScreen,
    'observation': ObservationScreen,
}


def load_screens() -> Dict[str, Any]:
    """ Initialize screen components and screens, and store references to them """
    for component_name in SCREEN_COMPONENTS:
        load_kv(component_name)

    screens = {}
    for screen_name, screen_cls in SCREENS.items():
        load_kv(screen_name)
        screens[screen_name] = screen_cls()
    return screens


def load_kv(name: str):
    """ Load an individual kv file by name """
    path = join(KV_SRC_DIR, f'{name}.kv')
    Builder.load_file(path)
    logger.debug(f'Init: Loaded {path}')
