from kivy.properties import BooleanProperty, NumericProperty
from kivymd.uix.button import MDFloatingActionButton, MDRoundFlatIconButton
from kivymd.uix.list import IconRightWidget
from kivymd.uix.tooltip import MDTooltip


class StarButton(IconRightWidget):
    """
    Selectable icon button that optionally toggles between 'selected' and 'unselected' star icons
    """

    taxon_id = NumericProperty()
    is_selected = BooleanProperty()

    def __init__(self, taxon_id, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.taxon_id = taxon_id
        self.is_selected = is_selected
        self.custom_icon = 'icon' in kwargs
        self.set_icon()

    def on_press(self):
        self.is_selected = not self.is_selected
        self.set_icon()

    def set_icon(self):
        if not self.custom_icon:
            self.icon = 'star' if self.is_selected else 'star-outline'


class TooltipFloatingButton(MDFloatingActionButton, MDTooltip):
    """ Floating action button class with tooltip behavior """


class TooltipIconButton(MDRoundFlatIconButton, MDTooltip):
    """ Flat button class with icon and tooltip behavior """
