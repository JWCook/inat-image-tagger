# TODO: This class has gotten large; split this up into at leeast two modules: taxon_select and taxon_view
import asyncio
from logging import getLogger
import webbrowser

from kivymd.uix.list import OneLineListItem, ThreeLineAvatarIconListItem, ImageLeftWidget

from naturtag.models import Taxon, get_icon_path
from naturtag.app import get_app
from naturtag.widgets import StarButton, TaxonListItem

logger = getLogger().getChild(__name__)


class TaxonViewController:
    """ Controller class to manage displaying info about a selected taxon """
    def __init__(self, screen):
        self.screen = screen

        # Other Controls
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
        self.basic_info = self.screen.basic_info_section

    def select_taxon(self, taxon_obj: Taxon=None, taxon_dict: dict=None, id: int=None, if_empty: bool=False):
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
        get_app().select_photo_taxon(self.selected_taxon.id)

    async def load_taxon_info(self):
        await asyncio.gather(
            self.load_photo_section(),
            self.load_basic_info_section(),
            self.load_ancestors(),
            self.load_children(),
        )

    async def load_photo_section(self):
        """ Load taxon photo + links """
        logger.info('Taxon: Loading photo section')
        if self.selected_taxon.photo_url:
            self.taxon_photo.source = self.selected_taxon.photo_url

        # Configure link to iNaturalist page
        self.taxon_link.bind(on_release=lambda *x: webbrowser.open(self.selected_taxon.link))
        self.taxon_link.tooltip_text = self.selected_taxon.link
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

    async def load_ancestors(self):
        """ Populate ancestors for the currently selected taxon """
        logger.info('Taxon: Loading ancestors')
        self.taxon_ancestors_label.text = _get_label('Ancestors', self.selected_taxon.parent_taxa)
        self.taxon_ancestors.clear_widgets()
        for taxon in self.selected_taxon.parent_taxa:
            self.taxon_ancestors.add_widget(self.get_taxon_list_item(taxon=taxon))
            await asyncio.sleep(0)

    async def load_children(self):
        """ Populate children for the currently selected taxon """
        logger.info('Taxon: Loading children')
        self.taxon_children_label.text = _get_label('Children', self.selected_taxon.child_taxa)
        self.taxon_children.clear_widgets()
        for taxon in self.selected_taxon.child_taxa:
            self.taxon_children.add_widget(self.get_taxon_list_item(taxon=taxon))
            await asyncio.sleep(0)

    def get_taxon_list_item(self, **kwargs):
        """ Get a taxon list item, with thumbnail + info, that selects its taxon when pressed """
        item = TaxonListItem(**kwargs)
        item.bind(on_release=lambda x: self.select_taxon(x.taxon))
        return item

    def on_star(self, button):
        """ Either add or remove a taxon from the starred list """
        if button.is_selected:
            get_app().add_star(self.selected_taxon.id)
        else:
            get_app().remove_star(self.selected_taxon.id)


def _get_label(text, items):
    return text + (f' ({len(items)})' if items else '')