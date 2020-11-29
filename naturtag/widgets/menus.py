from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy_garden.contextmenu import AbstractMenuItemHoverable, ContextMenu, ContextMenuText


class ObjectContextMenu(ContextMenu):
    """Context menu with a reference to an object, which can be set by an event handler on the
    parent controller
    """

    ref = ObjectProperty()


class AutoHideMenuItem(ButtonBehavior, ContextMenuText, AbstractMenuItemHoverable):
    """ Menu item that hides its parent menu after selecting """

    def on_release(self, *args):
        super().on_release()
        self.parent.hide()


class PhotoContextMenuItem(AutoHideMenuItem):
    """Menu item that has a reference to an image and its metadata
    (partly just to be more explicit/readable)
    """

    @property
    def selected_image(self):
        return self.parent.ref

    @property
    def metadata(self):
        return self.parent.ref.metadata_config


class ListContextMenuItem(AutoHideMenuItem):
    @property
    def list_item(self):
        return self.parent.ref

    @property
    def taxon_id(self):
        return self.parent.ref.taxon.id
