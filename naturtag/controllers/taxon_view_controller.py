import asyncio
import webbrowser
from logging import getLogger
from typing import List

from kivymd.uix.list import ImageLeftWidget, OneLineListItem, ThreeLineAvatarIconListItem

from naturtag.app import get_app
from naturtag.controllers import Controller, TaxonBatchLoader
from naturtag.models import Taxon, get_icon_path
from naturtag.widgets import StarButton

logger = getLogger().getChild(__name__)


class TaxonViewController(Controller):
    """ Controller class to manage displaying info about a selected taxon """

    def __init__(self, screen):
        super().__init__(screen)

        # Controls
        self.taxon_link = screen.taxon_links.ids.selected_taxon_link_button
        self.taxon_parent_button = screen.taxon_links.ids.taxon_parent_button
        self.taxon_parent_button.bind(on_release=lambda x: self.select_taxon(x.taxon.parent))

        # Outputs
        self.selected_taxon = None
        self.taxon_photo = screen.selected_taxon_photo
        self.taxon_ancestors_label = screen.taxonomy_section.ids.taxon_ancestors_label
        self.taxon_children_label = screen.taxonomy_section.ids.taxon_children_label
        self.taxon_ancestors = screen.taxonomy_section.ids.taxon_ancestors
        self.taxon_children = screen.taxonomy_section.ids.taxon_children
        self.basic_info = screen.basic_info_section

    def select_taxon(
        self,
        taxon_obj: Taxon = None,
        taxon_dict: dict = None,
        id: int = None,
        if_empty: bool = False,
    ):
        """ Update taxon info display by either object, ID, partial record, or complete record """
        # Initialize from object, dict, or ID
        if if_empty and self.selected_taxon is not None:
            return
        if not any([taxon_obj, taxon_dict, id]):
            return
        if not taxon_obj:
            taxon_obj = Taxon.from_dict(taxon_dict) if taxon_dict else Taxon.from_id(int(id))
        # Don't need to do anything if this taxon is already selected
        if self.selected_taxon is not None and taxon_obj.id == self.selected_taxon.id:
            return

        logger.info(f'Taxon: Selecting taxon {taxon_obj.id}')
        self.basic_info.clear_widgets()
        self.selected_taxon = taxon_obj
        asyncio.run(self.load_taxon_info())

        # Add to taxon history, and update taxon id on image selector screen
        get_app().update_history(self.selected_taxon.id)
        get_app().select_taxon_from_photo(self.selected_taxon.id)

    async def load_taxon_info(self):
        await asyncio.gather(
            self.load_photo_section(),
            self.load_basic_info_section(),
            self.load_taxonomy(),
        )

    async def load_photo_section(self):
        """ Load taxon photo + links """
        logger.info('Taxon: Loading photo section')
        if self.selected_taxon.default_photo.medium_url:
            self.taxon_photo.source = self.selected_taxon.default_photo.medium_url

        # Configure link to iNaturalist page
        self.taxon_link.bind(on_release=lambda *x: webbrowser.open(self.selected_taxon.uri))
        self.taxon_link.tooltip_text = self.selected_taxon.uri
        self.taxon_link.disabled = False

        # Configure 'View parent' button
        if self.selected_taxon.parent:
            self.taxon_parent_button.disabled = False
            self.taxon_parent_button.taxon = self.selected_taxon
            self.taxon_parent_button.tooltip_text = f'Go to {self.selected_taxon.parent.name}'
        else:
            self.taxon_parent_button.disabled = True
            self.taxon_parent_button.tooltip_text = ''

    async def load_basic_info_section(self):
        """ Load basic info for the currently selected taxon """
        # Name, rank
        logger.info('Taxon: Loading basic info section')
        item = ThreeLineAvatarIconListItem(
            text=self.selected_taxon.name,
            secondary_text=self.selected_taxon.rank.title(),
            tertiary_text=self.selected_taxon.preferred_common_name,
        )

        # Icon (if available)
        icon_path = get_icon_path(self.selected_taxon.iconic_taxon_id)
        if icon_path:
            item.add_widget(ImageLeftWidget(source=icon_path))
        self.basic_info.add_widget(item)

        # Star Button
        star_icon = StarButton(
            self.selected_taxon.id,
            is_selected=get_app().is_starred(self.selected_taxon.id),
        )
        star_icon.bind(on_release=self.on_star)
        item.add_widget(star_icon)

        # Other attrs
        for k in ['id', 'is_active', 'observations_count', 'complete_species_count']:
            label = k.title().replace('_', ' ')
            value = getattr(self.selected_taxon, k)
            item = OneLineListItem(text=f'{label}: {value}')
            self.basic_info.add_widget(item)

    async def load_taxonomy(self):
        """ Populate ancestors and children for the currently selected taxon """
        total_taxa = len(self.selected_taxon.parent_taxa) + len(self.selected_taxon.child_taxa)

        # Set up batch loader + event bindings
        if self.loader:
            self.loader.cancel()
        self.loader = TaxonBatchLoader()
        self.start_progress(total_taxa, self.loader)

        # Start loading ancestors
        logger.info(f'Taxon: Loading {len(self.selected_taxon.parent_taxa)} ancestors')
        self.taxon_ancestors_label.text = _get_label('Ancestors', self.selected_taxon.parent_taxa)
        self.taxon_ancestors.clear_widgets()
        self.loader.add_batch(self.selected_taxon.parent_taxa_ids, parent=self.taxon_ancestors)

        logger.info(f'Taxon: Loading {len(self.selected_taxon.child_taxa)} children')
        self.taxon_children_label.text = _get_label('Children', self.selected_taxon.child_taxa)
        self.taxon_children.clear_widgets()
        self.loader.add_batch(self.selected_taxon.child_taxa_ids, parent=self.taxon_children)

        self.loader.start_thread()

    def on_star(self, button):
        """ Either add or remove a taxon from the starred list """
        if button.is_selected:
            get_app().add_star(self.selected_taxon.id)
        else:
            get_app().remove_star(self.selected_taxon.id)


def _get_label(text: str, items: List) -> str:
    return text + (f' ({len(items)})' if items else '')
