from kivy.properties import ListProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.tooltip import MDTooltip


# TODO: Debug root cause of rogue tooltips!
class HideableTooltip(MDTooltip):
    """
    This is a workaround for unexpected behavior with tooltips and tabs. If a HideableTooltip is
    in an unselected tab, it will always report that the mouse cursor does not intersect it.
    """

    def __init__(self, is_visible_callback, **kwargs):
        self.is_visible_callback = is_visible_callback
        super().__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if self.is_visible_callback():
            super().on_mouse_pos(*args)


class TooltipLabel(MDLabel, MDTooltip):
    """ Label class with tooltip behavior """

    # Bug workaround; a fix has been committed, but not released
    padding = ListProperty([0, 0, 0, 0])
