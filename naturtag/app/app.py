""" Main Kivy application """
import asyncio
import os
from logging import getLogger
from threading import Thread

# Set GL backend before any kivy modules are imported
from kivy.clock import Clock

os.environ['KIVY_GL_BACKEND'] = 'sdl2'

# Disable multitouch emulation before any other kivy modules are imported
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from kivymd.app import MDApp

from naturtag.app import alert
from naturtag.app.screens import HOME_SCREEN, Root, load_screens
from naturtag.constants import (
    ATLAS_APP_ICONS,
    BACKSPACE,
    ENTER,
    F11,
    INIT_WINDOW_POSITION,
    INIT_WINDOW_SIZE,
    MD_ACCENT_PALETTE,
    MD_PRIMARY_PALETTE,
    TRIGGER_DELAY,
)
from naturtag.controllers import (
    CacheController,
    ImageSelectionController,
    MetadataViewController,
    SettingsController,
    TaxonSearchController,
    TaxonSelectionController,
    TaxonViewController,
)
from naturtag.inat_metadata import get_ids_from_url
from naturtag.widgets import TaxonListItem

logger = getLogger().getChild(__name__)


class ControllerProxy:
    """The individual controllers need to talk to each other sometimes.
    Any such interactions go through this class so they don't talk to each other directly.
    This also just serves as documentation for these interactions so I don't lose track of them.
    """

    image_selection_controller = ObjectProperty()
    metadata_view_controller = ObjectProperty()
    taxon_search_controller = ObjectProperty()
    taxon_selection_controller = ObjectProperty()
    taxon_view_controller = ObjectProperty()
    settings_controller = ObjectProperty()

    def init_controllers(self, screens):
        # Init controllers with references to nested screen objects
        self.cache_controller = CacheController(screens['cache'].ids)
        self.image_selection_controller = ImageSelectionController(screens[HOME_SCREEN].ids)
        self.metadata_view_controller = MetadataViewController(screens['metadata'].ids)
        self.settings_controller = SettingsController(screens['settings'].ids)
        self.taxon_search_controller = TaxonSearchController(screens['taxon'].ids)
        self.taxon_selection_controller = TaxonSelectionController(screens['taxon'].ids)
        self.taxon_view_controller = TaxonViewController(screens['taxon'].ids)
        # observation_search_controller = ObservationSearchController(screens['observation'].ids)

        # Proxy methods
        self.add_control_widget = self.settings_controller.add_control_widget
        self.add_star = self.taxon_selection_controller.add_star
        self.is_observed = self.settings_controller.is_observed
        self.is_starred = self.taxon_selection_controller.is_starred
        self.refresh_history = self.taxon_selection_controller.post_init
        self.refresh_observed_taxa = self.taxon_selection_controller.refresh_observed_taxa_tab
        self.remove_star = self.taxon_selection_controller.remove_star
        self.save_settings = self.settings_controller.save_settings
        self.select_metadata = self.metadata_view_controller.select_metadata
        self.select_taxon = self.taxon_view_controller.select_taxon
        self.select_taxon_from_photo = self.image_selection_controller.select_taxon_from_photo
        self.update_history = self.taxon_selection_controller.update_history

        self.image_selection_controller.post_init()
        self.taxon_selection_controller.post_init()

    def get_taxon_list_item(self, *args, **kwargs):
        """ Get a new :py:class:`.TaxonListItem with event binding """
        item = TaxonListItem(*args, **kwargs)
        self.bind_to_select_taxon(item)
        return item

    def bind_to_select_taxon(self, item):
        # If TaxonListItem's disable_button is set, don't set button action
        if not item.disable_button:
            item.bind(on_release=lambda x: self.taxon_view_controller.select_taxon(x.taxon))


class NaturtagApp(MDApp, ControllerProxy):
    """Manages window, theme, main screen and navigation state; other application logic is
    handled by Controller
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_loop = None
        self.root = None
        self.nav_drawer = None
        self.screen_manager = None
        self.toolbar = None

        # Buffer + delayed trigger For collecting multiple files dropped at once
        self.dropped_files = []
        self.drop_trigger = Clock.create_trigger(self.process_dropped_files, TRIGGER_DELAY)

    def build(self):
        # Create an event loop to be used by background loaders
        self.bg_loop = asyncio.new_event_loop()
        Thread(target=self.bg_loop.run_forever).start()
        self.theme_cls.theme_style = 'Dark'

        # Init screens and store references to them
        screens = load_screens()
        self.root = Root()
        ControllerProxy.init_controllers(self, screens)

        # Init screen manager and nav elements
        self.nav_drawer = self.root.ids.nav_drawer
        self.screen_manager = self.root.ids.screen_manager
        self.toolbar = self.root.ids.toolbar

        for screen_name, screen in screens.items():
            self.screen_manager.add_widget(screen)
        self.set_theme_mode()
        self.home()
        # self.switch_screen('taxon')

        # Set Window and theme settings
        position, left, top = INIT_WINDOW_POSITION
        Window.position = position
        Window.left = left
        Window.top = top
        Window.size = INIT_WINDOW_SIZE
        Window.bind(on_keyboard=self.on_keyboard)
        Window.bind(on_request_close=self.on_request_close)
        self.theme_cls.primary_palette = MD_PRIMARY_PALETTE
        self.theme_cls.accent_palette = MD_ACCENT_PALETTE

        # On_dropfile sends a single file at a time; this collects files dropped at the same time
        Window.bind(on_dropfile=lambda _, path: self.dropped_files.append(path))
        Window.bind(on_dropfile=self.drop_trigger)

        # Preload atlases so they're immediately available in Kivy cache
        Image(source=f'{ATLAS_APP_ICONS}/')
        # Image(source=f'{ATLAS_TAXON_ICONS}/')
        return self.root

    def process_dropped_files(self, *args):
        self.image_selection_controller.add_images(self.dropped_files)
        self.dropped_files = []

    def home(self, *args):
        self.switch_screen(HOME_SCREEN)

    def open_nav(self, *args):
        self.nav_drawer.set_state('open')

    def close_nav(self, *args):
        self.nav_drawer.set_state('close')

    def switch_screen(self, screen_name: str):
        # If we're leaving a screen with stored state, save it first
        # TODO: Also save stored taxa, but needs optimization first (async, only store if changed)
        if self.screen_manager.current in ['settings']:
            self.settings_controller.save_settings()

        self.screen_manager.current = screen_name
        self.update_toolbar(screen_name)
        self.close_nav()

    def on_request_close(self, *args):
        """ Save any unsaved settings before exiting """
        self.settings_controller.save_settings()
        self.stop()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """ Handle keyboard shortcuts """
        if (modifier, key) == (['ctrl'], BACKSPACE):
            self.home()
        elif (modifier, key) == (['ctrl'], ENTER):
            self.current_screen_action()
        elif (set(modifier), codepoint) == ({'ctrl', 'shift'}, 'x'):
            self.current_screen_clear()
        elif (modifier, codepoint) == (['ctrl'], 'o'):
            self.image_selection_controller.open_native_file_chooser()
        elif (set(modifier), codepoint) == ({'ctrl', 'shift'}, 'o'):
            self.image_selection_controller.open_native_file_chooser(dirs=True)
        elif (modifier, codepoint) == (['ctrl'], 'q'):
            self.on_request_close()
        elif (modifier, codepoint) == (['ctrl'], 's'):
            self.switch_screen('settings')
        elif (modifier, codepoint) == (['ctrl'], 't'):
            self.switch_screen('taxon')
        elif (modifier, codepoint) == (['ctrl'], 'v'):
            self.current_screen_paste()
        elif key == F11:
            self.toggle_fullscreen()

    # TODO: current_screen_*() may be better organized as controller methods (inherited/overridden as needed)
    def current_screen_action(self):
        """ Run the current screen's main action """
        if self.screen_manager.current == HOME_SCREEN:
            self.image_selection_controller.run()
        elif self.screen_manager.current == 'taxon':
            self.taxon_search_controller.search()

    def current_screen_clear(self):
        """ Clear the settings on the current screen, if applicable """
        if self.screen_manager.current == HOME_SCREEN:
            self.image_selection_controller.clear()
        elif self.screen_manager.current == 'taxon':
            self.taxon_search_controller.reset_all_search_inputs()

    def current_screen_paste(self):
        value = Clipboard.paste()
        taxon_id, observation_id = get_ids_from_url(value)
        if taxon_id:
            self.select_taxon(id=taxon_id)
            alert(f'Taxon {taxon_id} selected')
        if observation_id:
            # self.select_observation(id=observation_id)
            alert(f'Observation {observation_id} selected')

        # TODO: With improved taxon & observation screen, the ID search fields may no longer be useful
        # if self.screen_manager.current == HOME_SCREEN:
        #     if observation_id:
        #         self.image_selection_controller.inputs.observation_id_input.text = str(
        #             observation_id
        #         )
        #         self.image_selection_controller.inputs.taxon_id_input.text = ''
        #     elif taxon_id:
        #         self.image_selection_controller.inputs.observation_id_input.text = ''
        #         self.image_selection_controller.inputs.taxon_id_input.text = str(taxon_id)

    def update_toolbar(self, screen_name: str):
        """ Modify toolbar in-place so it can be shared by all screens """
        self.toolbar.title = screen_name.title().replace('_', ' ')
        if screen_name == HOME_SCREEN:
            self.toolbar.left_action_items = [['menu', self.open_nav]]
        else:
            self.toolbar.left_action_items = [["arrow-left", self.home]]
        self.toolbar.right_action_items = [
            ['fullscreen', self.toggle_fullscreen],
            ['dots-vertical', self.open_settings],
        ]

    def set_theme_mode(self, switch=None, is_active: bool = None):
        """ Set light or dark themes, based on either toggle switch or settings """
        if is_active is None:
            is_active = self.settings_controller.display['dark_mode']
        self.theme_cls.theme_style = 'Dark' if is_active else 'Light'

    def toggle_fullscreen(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        if Window.fullscreen:
            Window.fullscreen = 0
            icon = 'fullscreen'
        else:
            Window.fullscreen = 'auto'
            icon = 'fullscreen-exit'
        self.toolbar.right_action_items[0] = [icon, self.toggle_fullscreen]


def main():
    NaturtagApp().run()


if __name__ == '__main__':
    main()
