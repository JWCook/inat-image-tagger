from kivy.properties import StringProperty
from kivymd.uix.menu import MDDropdownMenu


class DropdownTextField(MDDropdownMenu):
    """ A dropdown menu class that includes basic interaction with a text input field """

    def __init__(self, *args, text_input=None, text_items=None, add_none_item=True, **kwargs):
        """
        To be more explicit, this adds an extra ``text_items`` parameter for text-only items, and
        ``text_input`` instead of ``caller``, as well as some size defaults
        """
        # Convert str list to dict, if specified
        if text_items:
            kwargs['items'] = [{'text': i} for i in text_items]
        # Add a 'None' item to the top of the list to deselect it
        if add_none_item:
            kwargs['items'].insert(0, {'text': 'None'})

        kwargs['callback'] = self.on_select
        kwargs['caller'] = text_input
        kwargs.setdefault('max_height', 400)
        kwargs.setdefault('width_mult', 4)
        kwargs.setdefault('hor_growth', 'right')

        self.text_input = text_input
        self.text_input.bind(focus=self.open_on_focus)
        super().__init__(*args, **kwargs)

    def open_on_focus(self, instance, *args):
        """ Open the dropdown if the given instance has focus """
        # Setting the text input before losing focus coerces the 'hint text' to behave as expected
        self.text_input.text = self.text_input.text or '  '
        if instance.focus:
            self.open()

    def on_dismiss(self):
        super().on_dismiss()
        # If we set whitespace as a placeholder but didn't select anything, revert
        if self.text_input.text == '  ':
            self.text_input.text = ''

    def on_select(self, dropdown_item):
        """ On clicking a dropdown item, populate the text field's text """
        # Selecting the 'None' item removes any previous selection
        self.text_input.text = dropdown_item.text.replace('None', '')
        self.dismiss()


class TextFieldWrapper:
    """Mixin for a class that wraps a :py:class:`.MDTextField` within another layout or widget.
    Properties set on the class will be passed along to the text field.
    """

    hint_text = StringProperty()
    helper_text = StringProperty()
    helper_text_mode = StringProperty()
    color_mode = StringProperty()
    icon_right = StringProperty()
    icon_right_color = StringProperty()

    def on_hint_text(self, instance, value):
        self.ids.text_input.hint_text = value

    def on_helper_text(self, instance, value):
        self.ids.text_input.helper_text = value

    def on_helper_text_mode(self, instance, value):
        self.ids.text_input.helper_text_mode = value

    def on_color_mode(self, instance, value):
        self.ids.text_input.color_mode = value

    def on_icon_right(self, instance, value):
        self.ids.text_input.icon_right = value

    def on_icon_right_color(self, instance, value):
        self.ids.text_input.icon_right_color = value
