import asyncio
from collections import OrderedDict
from logging import getLogger

from kivy.clock import Clock

from naturtag.app import get_app, alert
from naturtag.constants import MAX_DISPLAY_HISTORY
from naturtag.controllers import Controller, TaxonBatchLoader
from naturtag.inat_metadata import get_user_taxa
from naturtag.widgets import StarButton, TaxonListItem

logger = getLogger().getChild(__name__)


# TODO: Better name for this? Maybe 'TaxonQuickAccessController'?
class TaxonSelectionController(Controller):
    """ Controller class to manage selecting stored taxa """

    def __init__(self, screen):
        super().__init__(screen)
        # Tab references
        self.history_tab = screen.history_tab
        self.frequent_tab = screen.frequent_tab
        self.starred_tab = screen.starred_tab

        # Context menu
        self.context_menu = screen.context_menu
        self.context_menu.ids.move_to_top_ctx.bind(on_release=self.move_starred_to_top)

        # Various taxon lists
        self.taxon_history_ids = []
        self.taxon_history_map = {}
        self.taxon_history_list = screen.history_tab.ids.taxon_history_list
        self.frequent_taxa_ids = {}
        self.frequent_taxa_list = screen.frequent_tab.ids.frequent_taxa_list
        self.frequent_taxa_list.sort_key = self.get_frequent_taxon_idx
        self.user_taxa_ids = {}
        self.user_taxa_map = {}
        self.user_taxa_list = screen.user_tab.ids.user_taxa_list
        self.starred_taxa_ids = []
        self.starred_taxa_map = {}
        self.starred_taxa_list = screen.starred_tab.ids.starred_taxa_list

    def post_init(self):
        Clock.schedule_once(lambda *x: asyncio.run(self.init_stored_taxa()), 1)

    async def init_stored_taxa(self):
        """ Load taxon history, starred, and frequently viewed items """
        logger.info('Loading stored taxa')
        stored_taxa = get_app().stored_taxa
        self.taxon_history_ids, self.starred_taxa_ids, self.frequent_taxa_ids = stored_taxa
        self.user_taxa_ids = self.get_user_taxa()

        # Collect all the taxon IDs we need to load
        unique_history = list(OrderedDict.fromkeys(self.taxon_history_ids[::-1]))[
            :MAX_DISPLAY_HISTORY
        ]
        starred_taxa_ids = self.starred_taxa_ids[::-1]
        top_frequent_ids = list(self.frequent_taxa_ids.keys())[:MAX_DISPLAY_HISTORY]
        top_user_ids = list(self.user_taxa_ids.keys())[:MAX_DISPLAY_HISTORY]
        total_taxa = sum(
            map(
                len,
                (
                    unique_history,
                    self.starred_taxa_ids,
                    top_user_ids,
                    top_frequent_ids,
                ),
            )
        )

        # Start progress bar with a new batch loader
        loader = TaxonBatchLoader()
        self.start_progress(total_taxa, loader)

        # Add the finishing touches after all items have loaded
        def index_list_items(*args):
            for item in self.taxon_history_list.children:
                self.taxon_history_map[item.taxon.id] = item
            for item in self.starred_taxa_list.children:
                self.bind_star(item)

        loader.bind(on_complete=index_list_items)

        # Start loading batches of TaxonListItems
        logger.info(
            f'Taxon: Loading {len(unique_history)} unique taxa from history'
            f' (from {len(self.taxon_history_ids)} total)'
        )
        loader.add_batch(unique_history, parent=self.taxon_history_list)
        logger.info(f'Taxon: Loading {len(starred_taxa_ids)} starred taxa')
        loader.add_batch(starred_taxa_ids, parent=self.starred_taxa_list)
        logger.info(f'Taxon: Loading {len(top_frequent_ids)} frequently viewed taxa')
        loader.add_batch(top_frequent_ids, parent=self.frequent_taxa_list)
        logger.info(f'Taxon: Loading {len(top_user_ids)} user-observed taxa')
        loader.add_batch(top_user_ids, parent=self.user_taxa_list)

        loader.start_thread()

    def update_history(self, taxon_id: int):
        """ Update history + frequency """
        self.taxon_history_ids.append(taxon_id)

        # If item already exists in history, move it from its previous position to the top
        if taxon_id in self.taxon_history_map:
            item = self.taxon_history_map[taxon_id]
            self.taxon_history_list.remove_widget(item)
        else:
            item = get_app().get_taxon_list_item(taxon_id)
            self.taxon_history_map[taxon_id] = item

        self.taxon_history_list.add_widget(item, len(self.taxon_history_list.children))
        self.add_frequent_taxon(taxon_id)

    def add_frequent_taxon(self, taxon_id: int):
        self.frequent_taxa_ids.setdefault(taxon_id, 0)
        self.frequent_taxa_ids[taxon_id] += 1
        self.frequent_taxa_list.sort()

    @staticmethod
    def get_user_taxa():
        username = get_app().username
        # TODO: Show this alert only when clicking on tab instead
        if not username:
            alert('Please enter iNaturalist username on Settings page')
            return {}
        return get_user_taxa(username)

    def add_star(self, taxon_id: int):
        """ Add a taxon to Starred list """
        logger.info(f'Adding taxon to starred: {taxon_id}')
        if taxon_id not in self.starred_taxa_ids:
            self.starred_taxa_ids.append(taxon_id)

        item = get_app().get_taxon_list_item(taxon_id, disable_button=True)
        self.starred_taxa_list.add_widget(item, len(self.starred_taxa_list.children))
        self.bind_star(item)

    def bind_star(self, item: TaxonListItem):
        """ Bind click events on a starred taxon list item, including an X (remove) button """
        item.bind(on_touch_down=self.on_starred_taxon_click)
        remove_button = StarButton(item.taxon.id, icon='close')
        remove_button.bind(on_release=lambda x: self.remove_star(x.taxon_id))
        item.add_widget(remove_button)
        self.starred_taxa_map[item.taxon.id] = item

    # TODO: Also remove star from info section if this taxon happens to be currently selected
    def remove_star(self, taxon_id: int):
        """ Remove a taxon from Starred list """
        logger.info(f'Removing taxon from starred: {taxon_id}')
        if taxon_id in self.starred_taxa_map:
            item = self.starred_taxa_map.pop(taxon_id)
            self.starred_taxa_ids.remove(taxon_id)
            self.starred_taxa_list.remove_widget(item)

    def is_starred(self, taxon_id: int) -> bool:
        """ Check if the specified taxon is in the Starred list """
        return taxon_id in self.starred_taxa_map

    def on_starred_taxon_click(self, instance, touch):
        """ Event handler for clicking a item from starred taxa list """
        if not instance.collide_point(*touch.pos):
            return
        # Right-click: Open context menu
        elif touch.button == 'right':
            self.context_menu.show(*get_app().root_window.mouse_pos)
            self.context_menu.ref = instance
            # self.context_menu.ids.view_taxon_ctx.disabled = not instance.metadata.taxon_id
        # Middle-click: remove item
        elif touch.button == 'middle':
            self.remove_star(instance.taxon.id)
        # Left-cliok: select taxon
        else:
            get_app().select_taxon(instance.taxon)

    def move_starred_to_top(self, instance):
        """ Move a starred taxon to the top of the list, both in the UI and in persisted list """
        lst = self.starred_taxa_ids
        lst.append(lst.pop(lst.index(instance.taxon_id)))
        item = self.starred_taxa_map[instance.taxon_id]
        self.starred_taxa_list.remove_widget(item)
        self.starred_taxa_list.add_widget(item, len(self.starred_taxa_list.children))

    def get_frequent_taxon_idx(self, list_item) -> int:
        """ Get sort index for frequently viewed taxa (by number of views, descending) """
        num_views = self.frequent_taxa_ids.get(list_item.taxon.id, 0)
        return num_views * -1  # Effectively the same as reverse=True
