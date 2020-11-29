from typing import Union

from kivy.core.clipboard import Clipboard
from kivymd.uix.list import (
    IconRightWidget,
    ILeftBody,
    ILeftBodyTouch,
    IRightBodyTouch,
    MDList,
    OneLineListItem,
    ThreeLineAvatarIconListItem,
)
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextFieldRound

from naturtag.app import alert, get_app
from naturtag.models import Taxon
from naturtag.widgets import CachedAsyncImage


class SortableList(MDList):
    """ List class that can be sorted by a custom sort key """

    def __init__(self, sort_key=None, **kwargs):
        self.sort_key = sort_key
        super().__init__(**kwargs)

    def sort(self):
        """ Sort child items in-place using current sort key """
        children = self.children.copy()
        self.clear_widgets()
        for child in sorted(children, key=self.sort_key):
            self.add_widget(child)


class SwitchListItemLeft(ILeftBodyTouch, MDSwitch):
    """ Switch that works as a list item """


class SwitchListItemRight(IRightBodyTouch, MDSwitch):
    """ Switch that works as a list item """


class TextInputListItem(OneLineListItem, MDTextFieldRound):
    """ Text input that works as a list item """


class TaxonListItem(ThreeLineAvatarIconListItem):
    """ Class that displays condensed taxon info as a list item """

    def __init__(
        self,
        taxon: Union[Taxon, int, dict] = None,
        disable_button: bool = False,
        highlight_observed: bool = True,
        **kwargs,
    ):
        if not taxon:
            raise ValueError('Must provide either a taxon object or ID')
        if isinstance(taxon, int):
            taxon = Taxon.from_id(taxon)
        elif isinstance(taxon, dict):
            taxon = Taxon.from_dict(taxon)
        self.taxon = taxon

        # Set click event unless disabled
        if not disable_button:
            self.bind(on_touch_down=self._on_touch_down)
        self.disable_button = disable_button

        super().__init__(
            font_style='H6',
            text=taxon.name,
            secondary_text=taxon.rank,
            tertiary_text=taxon.preferred_common_name,
            **kwargs,
        )

        # Add thumbnail
        self.add_widget(
            ThumbnailListItem(source=taxon.default_photo.thumbnail_url or taxon.icon_path)
        )
        # Add user icon if taxon has been observed by the user
        if highlight_observed and get_app().is_observed(taxon.id):
            self.add_widget(IconRightWidget(icon='account-search'))

    def _on_touch_down(self, instance, touch):
        """ Copy text on right-click """
        if not self.collide_point(*touch.pos):
            return
        elif touch.button == 'right':
            Clipboard.copy(self.text)
            alert('Copied to clipboard')
        else:
            super().on_touch_down(touch)


class ThumbnailListItem(CachedAsyncImage, ILeftBody):
    """ Class that contains a taxon thumbnail to be used in a list item """

    def __init__(self, **kwargs):
        super().__init__(thumbnail_size='small', **kwargs)
