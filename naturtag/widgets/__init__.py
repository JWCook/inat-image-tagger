"""
Custom widgets with more complex behavior that can't be defined in just kvlang.
See widgets.kv for non-behavioral widget settings
"""
# flake8: noqa: F401


# Not sure where else to put thus
def truncate(text: str) -> str:
    """ Truncate a label string to not exceed maximum length """
    if len(text) > MAX_LABEL_CHARS:
        text = text[: MAX_LABEL_CHARS - 2] + '...'
    return text


from naturtag.constants import MAX_LABEL_CHARS
from naturtag.widgets.autocomplete import AutocompleteSearch, DropdownContainer, DropdownItem
from naturtag.widgets.buttons import StarButton, TooltipFloatingButton, TooltipIconButton
from naturtag.widgets.images import CachedAsyncImage, IconicTaxaIcon, ImageMetaTile
from naturtag.widgets.inputs import DropdownTextField, TextFieldWrapper
from naturtag.widgets.labels import HideableTooltip, TooltipLabel
from naturtag.widgets.lists import (
    SortableList,
    SwitchListItemLeft,
    SwitchListItemRight,
    TaxonListItem,
    TextInputListItem,
    ThumbnailListItem,
)
from naturtag.widgets.menus import (
    AutoHideMenuItem,
    ListContextMenuItem,
    ObjectContextMenu,
    PhotoContextMenuItem,
)
from naturtag.widgets.progress_bar import LoaderProgressBar
from naturtag.widgets.tabs import Tab
from naturtag.widgets.taxon_autocomplete import TaxonAutocompleteSearch
