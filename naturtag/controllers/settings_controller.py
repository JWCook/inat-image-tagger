import webbrowser
from datetime import datetime
from locale import getdefaultlocale
from logging import getLogger
from typing import Dict, List, Tuple

from kivy.uix.widget import Widget
from kivymd.app import MDApp

from naturtag.app import alert
from naturtag.constants import OBS_CACHE_EXPIRY_HOURS, PLACES_BASE_URL
from naturtag.controllers import Controller
from naturtag.settings import (
    read_settings,
    read_stored_taxa,
    reset_defaults,
    write_settings,
    write_stored_taxa,
)
from naturtag.validation import is_expired

logger = getLogger(__name__)


# TODO: Track whether state changed since last write; if not, don't write on close
class SettingsController(Controller):
    """ Controller class to manage Settings screen, and reading from and writing to settings file """

    def __init__(self, settings_screen):
        self.screen = settings_screen
        self.settings_dict = read_settings()
        self._stored_taxa = read_stored_taxa()

        # Set default locale if it's unset
        if self.inaturalist['locale'] is None:
            self.inaturalist['locale'] = getdefaultlocale()[0]

        self.screen.preferred_place_id_label.bind(
            on_release=lambda *x: webbrowser.open(PLACES_BASE_URL)
        )
        self.screen.dark_mode_chk.bind(active=MDApp.get_running_app().set_theme_mode)
        self.screen.reset_default_button.bind(on_release=self.clear_settings)

        # Control widget ids should match the options in the settings file (with suffixes)
        self.controls = {
            id.replace('_chk', '').replace('_input', ''): getattr(settings_screen, id)
            for id in settings_screen
        }
        self.update_control_widgets()

    def add_control_widget(self, widget: Widget, setting_name: str, section: str):
        """ Add a control widget from another screen, so its state will be stored with app settings """
        self.controls[setting_name] = widget
        value = self.settings_dict.get(section, {}).get(setting_name)
        self.set_control_value(setting_name, value)
        # Initialize section and setting if either have never been set before
        self.settings_dict.setdefault(section, {})
        self.settings_dict[section].setdefault(setting_name, value)

    def clear_settings(self, *args):
        reset_defaults()
        self.update_control_widgets()
        alert('Settings have been reset to defaults')

    @property
    def stored_taxa(self) -> Tuple[List[int], List[int], Dict[int, int], Dict[int, int]]:
        return (
            self._stored_taxa['history'],
            self._stored_taxa['starred'],
            self._stored_taxa['frequent'],
            self._stored_taxa['observed'],
        )

    def update_control_widgets(self):
        """ Update state of settings controls in UI with values from settings file """
        logger.info(f'Settings: Loading settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name, value in section.items():
                self.set_control_value(setting_name, value)

    def save_settings(self):
        """ Save the current state of the control widgets to settings file """
        logger.info(f'Settings: Saving settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name in section.keys():
                value = self.get_control_value(setting_name)
                if value is not None:
                    section[setting_name] = value

        write_settings(self.settings_dict)
        write_stored_taxa(self._stored_taxa)

    def get_control_value(self, setting_name):
        """ Get the value of the control widget corresponding to a setting """
        control_widget, property, _ = self.get_control_widget(setting_name)
        return getattr(control_widget, property) if control_widget else None

    def set_control_value(self, setting_name, value):
        """ Set the value of the control widget corresponding to a setting """
        control_widget, property, setting_type = self.get_control_widget(setting_name)
        if control_widget:
            setattr(control_widget, property, setting_type(value))

    def get_control_widget(self, setting_name):
        """  Find the widget corresponding to a setting and detect its type (bool, str, int) """
        # The setting (from file) may not have a corresponding widget on the Settings screen
        if setting_name not in self.controls:
            return None, None, None

        control_widget = self.controls[setting_name]
        if hasattr(control_widget, 'active'):
            return control_widget, 'active', bool
        elif hasattr(control_widget, 'text'):
            return control_widget, 'text', str
        if hasattr(control_widget, 'path'):
            return control_widget, 'path', str
        else:
            logger.warning(f'Settings: Could not detect type for {control_widget}')

    def is_observed(self, taxon_id: int):
        """Determine if the specified taxon has been observed by the user"""
        return taxon_id in self._stored_taxa['observed']

    def is_observed_taxa_expired(self):
        """Determine if local cache of user-observed taxa has expired"""
        return is_expired(
            self._stored_taxa.get("last_updated_observations"), OBS_CACHE_EXPIRY_HOURS
        )

    def update_observed_taxa(self, observed_taxa_ids: Dict[int, int]):
        """Save updated user-observed taxa"""
        self._stored_taxa["observed"] = observed_taxa_ids
        self._stored_taxa["last_updated_observations"] = datetime.now().isoformat()
        write_stored_taxa(self._stored_taxa)

    @property
    def locale(self):
        return self.inaturalist.get('locale')

    @property
    def username(self):
        return self.inaturalist.get('username')

    @property
    def preferred_place_id(self):
        return self.inaturalist.get('preferred_place_id')

    @property
    def inaturalist(self):
        return self.settings_dict['inaturalist']

    @property
    def metadata(self):
        return self.settings_dict['metadata']

    @property
    def display(self):
        return self.settings_dict['display']
