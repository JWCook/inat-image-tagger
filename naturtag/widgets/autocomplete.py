"""
Generic/reusable autocomplete search + dropdown components
Since this has 5+ levels of nested widgets, here's an overview of what they do:

AutocompleteController:         : Manages interactions between input, search, and dropdown
    TextInput                   : Text input for search
    DropdownContainer           : Wraps contents with resizing, 'open' and 'dismiss' functionality
        RecycleView             : Manages displaying (a subset of) frequently-changing contents
            DropdownLayout      : Adds selection behavior + selection event
                DropdownItem    : Individual selectable search results
                DropdownItem
                ...
"""
import asyncio
from collections.abc import Mapping
from logging import getLogger

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from naturtag.app.screens import load_kv
from naturtag.constants import AUTOCOMPLETE_DELAY, AUTOCOMPLETE_MIN_CHARS
from naturtag.widgets import TextFieldWrapper

PADDING = dp(50)
ROW_SIZE = dp(22)
logger = getLogger().getChild(__name__)
load_kv('autocomplete')


class AutocompleteSearch(MDBoxLayout, TextFieldWrapper):
    """
    Class containing all components needed for autocomplete search.
    This manages an input field and a dropdown, so they don't interact with each other directly.
    Also includes rate-limited trigger for input delay (so we don't spam searches on every keypress).

    Must be inherited by a subclass that implements :py:meth:`get_autocomplete`.

    Events:
        on_selection: Called when a result is selected from the dropdown list
    """

    def __init__(self, text_input_kwargs=None, **kwargs):
        """
        Args:
            text_input_kwargs: Optional settings for :py:class:`.MDTextField`
        """
        super().__init__(**kwargs)
        self.register_event_type('on_selection')
        self.trigger = Clock.create_trigger(self.callback, AUTOCOMPLETE_DELAY)
        Clock.schedule_once(lambda *x: self.post_init(text_input_kwargs or {}))

    def post_init(self, text_input_kwargs):
        """ Finish initialization after populating children (otherwise self.ids will be empty """
        self.text_input = self.ids.text_input
        self.text_input.bind(
            text=lambda *x: self.trigger(),
            focus=self.on_text_focus,
        )
        self.ids.clear_input_button.bind(on_release=self.reset)

        if text_input_kwargs:
            logger.debug(f'Overriding text input settings: {text_input_kwargs}')
            for k, v in text_input_kwargs.items():
                setattr(self.text_input, k, v)

        self.dropdown_container = self.ids.dropdown_container
        self.dropdown_view = self.ids.dropdown_view
        self.ids.dropdown_layout.bind(on_selection=lambda *x: self.update_selection(*x))

    def on_text_focus(self, instance, *args):
        """ Re-open dropdown after clicking on input again (if there are previous results) """
        if instance.focus:
            logger.debug('Opening dropdown on text focus')
            self.dropdown_container.open()

    def callback(self, *args):
        """ Autocompletion callback, rate-limited by ``AUTOCOMPLETE_DELAY`` milliseconds """
        logger.debug('Populating autocomplete results')
        search_str = self.text_input.text
        if len(search_str) < AUTOCOMPLETE_MIN_CHARS:
            return

        def get_row(item):
            """ Return a row for dropdown list; use optional metadata if provided """
            if isinstance(item, Mapping):
                return item
            return {'text': item, 'suggestion_text': item, 'metadata': {}}

        matches = asyncio.run(self.get_autocomplete(search_str))
        logger.info(f'Found {len(matches)} matches for search string "{search_str}"')
        self.dropdown_view.data = [get_row(i) for i in matches]
        self.dropdown_container.open()

    # TODO: formatting for suggestion_text; smaller text + different color
    def update_selection(self, instance, suggestion_text, metadata):
        """ Intermediate handler to update suggestion text based on dropdown selection """
        self.text_input.suggestion_text = '    ' + suggestion_text
        self.dispatch('on_selection', metadata)
        Clock.schedule_once(self.dropdown_container.dismiss, 0.2)

    def on_selection(self, metadata):
        """  Called when a result is selected from the dropdown list """

    async def get_autocomplete(self, search_str):
        """
        Autocompletion behavior to be implemented by a subclass. There are two return format options:

        1. Just return a list of strings representing match text to display
        2. Return a dict with additional info:
            * The text to display in the dropdown
            * The text to place in ``suggestion_text`` when selected
            * A dict of additional metadata to be retrieved when selected

        Example::

            [
                {'text': display_text, 'suggestion_text': suggestion_text, 'metadata': metadata},
            ]

        Args:
            search_str (str): Search string to fetch matches for

        Returns:
            list: List of either match strings, or dicts with additional metadata
        """
        return [{'text': f'Text: {search_str}'}] + [{'text': f'Text: {i}'} for i in range(9)]

    def reset(self, *args):
        """ Reset inputs and autocomplete results """
        self.text_input.text = ''
        self.text_input.suggestion_text = ''
        self.dropdown_view.data = []


class DropdownContainer(MDCard):
    """Container layout that handles positioning & sizing of contents, and wraps with
    'open' and 'dismiss' functionality
    """

    caller = ObjectProperty()
    layout = ObjectProperty()
    view = ObjectProperty()
    max_height = NumericProperty(500)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(
            on_resize=self.on_window_resize,
            on_restore=self.on_window_resize,
            on_maximize=self.on_window_resize,
        )
        self._resize_complete = False
        self.start_coords = [0, 0]
        self._data = []
        self.is_open = False

    def on_window_resize(self, *args):
        """When the window is resized, re-calculate properties.
        If the dropdown is open, resize now; otherwise, delay until re-opened.
        """
        self._resize_complete = False
        if self.is_open:
            self.resize_layout()

    def resize_layout(self):
        """ Adjust size of layout to fit contents """
        self.start_coords = self.caller.to_window(*self.caller.pos)
        self.layout.size_hint_min_y = ROW_SIZE * len(self.view.data)
        # If data hasn't been set yet, resize again when set
        if self.view.data:
            self._resize_complete = True

    def open(self):
        """ Open dropdown """
        logger.debug(f'Opening dropdown at {self.layout.center_x}, {self.layout.center_y}')
        if not self._resize_complete:
            self.resize_layout()
        # Re-opening without any changes to data
        if self._data and not self.view.data:
            self.view.data = self._data
        self.is_open = True

    def on_touch_down(self, touch):
        """ Close the dropdown if we click off of it """
        if not self.is_open or self.view.collide_point(*touch.pos):
            super().on_touch_down(touch)
        else:
            self.dismiss()

    def dismiss(self, *args):
        """ Close dropdown, and temporarily store data and remove from RecycleView to resize it """
        if self.view.data:
            self._data = self.view.data
            self.view.data = []
        self.is_open = False


class DropdownLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """
    Class that adds selection and focus behaviour to a dropdown list. Using a RecycleBoxLayout
    because other options (like :py:class:`.MDDropdownList`) are inefficient for frequently
    changing contents.

    Events:
        on_selection: Called when a result is selected from the dropdown list
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_selection')

    def on_selection(self, suggestion_text, metadata):
        """  Called when a result is selected from the dropdown list """


class DropdownItem(RecycleDataViewBehavior, MDLabel):
    """
    A label representing a dropdown item, which handles click events.
    Optionally contains additional metadata to associate with the item.
    """

    index = None
    selectable = True
    is_selected = BooleanProperty(False)
    suggestion_text = StringProperty()
    metadata = DictProperty()

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle view changes """
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on click. ``on_selection`` event is raised here instead of in
        :py:meth:`.apply_selection` in order to handle only real selection events and not
        automatic selection checks.
        """
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            logger.debug(f'Selecting item {self.text}')
            self.parent.select_with_touch(self.index, touch)
            self.parent.dispatch('on_selection', self.suggestion_text, self.metadata)
            return True

    def apply_selection(self, dropdown_view, index, is_selected):
        """ Respond to the selection of items in the view """
        self.is_selected = is_selected


class SearchInput(MDTextField):
    """ A text input field for autocomplete search """

    # TODO: Not yet working as intended
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        """ Select an autocomplete match with the tab key """
        if self.suggestion_text and keycode[1] == 'tab':
            self.insert_text(self.suggestion_text + ' ')
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)
