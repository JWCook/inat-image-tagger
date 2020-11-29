from logging import getLogger

import requests_cache
from kivy.clock import Clock

from naturtag.app import alert, get_app
from naturtag.controllers import Controller
from naturtag.inat_metadata import get_http_cache_size
from naturtag.thumbnails import delete_thumbnails, get_thumbnail_cache_size

logger = getLogger(__name__)


class CacheController(Controller):
    """ Controller class to manage Settings screen, and reading from and writing to settings file """

    def __init__(self, cache_screen):
        self.screen = cache_screen

        # Bind buttons
        self.screen.cache_size_output.bind(on_release=self.update_cache_sizes)
        self.screen.clear_request_cache_button.bind(on_release=self.clear_http_cache)
        self.screen.clear_thumbnail_cache_button.bind(on_release=self.clear_thumbnail_cache)
        self.screen.clear_history_button.bind(on_release=self.clear_history)
        self.screen.refresh_observed_taxa_button.bind(on_release=self.refresh_observed_taxa)

        Clock.schedule_once(self.update_cache_sizes, 5)

    def clear_history(self, *args):
        logger.info('Settings: Clearing history')
        history, _, frequent, _ = get_app().settings_controller.stored_taxa
        history.clear()
        frequent.clear()

        # Update everything that refers to history/frequent items
        get_app().save_settings()
        get_app().refresh_history()
        self.update_cache_sizes()
        alert('History has been cleared')

    def clear_http_cache(self, *args):
        logger.info('Settings: Clearing HTTP request cache')
        requests_cache.clear()
        self.update_cache_sizes()
        alert('Cache has been cleared')

    def clear_thumbnail_cache(self, *args):
        logger.info('Settings: Clearing thumbnail cache')
        delete_thumbnails()
        self.update_cache_sizes()
        alert('Cache has been cleared')

    @staticmethod
    def refresh_observed_taxa(*args):
        get_app().refresh_observed_taxa()
        alert('Refreshing observed species...')

    def update_cache_sizes(self, *args):
        """Populate 'Cache Size' sections with calculated totals"""
        out = self.screen.cache_size_output

        out.text = f'Request cache size: {get_http_cache_size()}'
        num_thumbs, thumbnail_total_size = get_thumbnail_cache_size()
        out.secondary_text = (
            f'Thumbnail cache size: {num_thumbs} files totaling {thumbnail_total_size}'
        )
        history, _, frequent, _ = get_app().settings_controller.stored_taxa
        out.tertiary_text = f'History: {len(history)} items ({len(frequent)} unique)'
