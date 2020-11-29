import asyncio
from logging import getLogger

from naturtag.app import alert, get_app
from naturtag.controllers import Controller, ImageBatchLoader
from naturtag.image_glob import get_images_from_paths
from naturtag.tagger import tag_images

logger = getLogger().getChild(__name__)


class ImageSelectionController(Controller):
    """ Controller class to manage image selector screen """

    def __init__(self, screen):
        super().__init__(screen)
        self.context_menu = screen.context_menu
        self.inputs = screen
        self.image_previews = screen.image_previews
        self.file_chooser = screen.file_chooser
        self.file_list = []
        self.theme_cls = get_app().theme_cls

        # Context menu item events
        self.context_menu.ids.view_taxon_ctx.bind(on_release=self.view_taxon)
        # self.context_menu.ids.view_observation_ctx.bind(on_release=self.view_observation)
        self.context_menu.ids.view_metadata_ctx.bind(on_release=self.view_metadata)
        self.context_menu.ids.copy_flickr_tags_ctx.bind(
            on_release=lambda x: x.selected_image.copy_flickr_tags()
        )
        self.context_menu.ids.remove_ctx.bind(
            on_release=lambda x: self.remove_image(x.selected_image)
        )

        # Other widget events
        self.inputs.taxon_id_input.bind(on_text_validate=self.on_taxon_id)
        self.inputs.clear_button.bind(on_release=self.clear)
        self.inputs.load_button.bind(on_release=self.add_file_chooser_images)
        self.inputs.run_button.bind(on_release=self.run)
        self.file_chooser.bind(on_submit=self.add_file_chooser_images)

    def post_init(self):
        # Load and save start dir from file chooser with the rest of the app settings
        get_app().add_control_widget(self.file_chooser, 'start_dir', 'photos')

    def add_file_chooser_images(self, *args):
        """ Add one or more files and/or dirs selected via a FileChooser """
        self.add_images(self.file_chooser.selection)

    def add_image(self, path):
        """ Add an image to the current selection """
        self.add_images([path])

    def add_images(self, paths):
        """ Add one or more files and/or dirs, with deduplication """
        asyncio.run(self.load_images(paths))

    async def load_images(self, paths):
        # Determine images to load, ignoring duplicates
        images = get_images_from_paths(paths, recursive=self.input_dict['recursive'])
        new_images = list(set(images) - set(self.file_list))
        logger.info(
            f'Main: Loading {len(new_images)} ({len(images) - len(new_images)} already loaded)'
        )
        if not new_images:
            return
        self.file_list.extend(new_images)

        # Start batch loader + progress bar
        loader = ImageBatchLoader()
        self.start_progress(len(new_images), loader)
        loader.add_batch(new_images, parent=self.image_previews)
        loader.start_thread()

    def open_native_file_chooser(self, dirs=False):
        """ A bit of a hack; uses a hidden tkinter window to open a native file chooser dialog """
        from tkinter import Tk
        from tkinter.filedialog import askdirectory, askopenfilenames

        Tk().withdraw()
        # Tkinter does not have a single dialog that combines directory and file selection >:[
        if dirs:
            paths = askdirectory(title='Choose an image directory')
        else:
            paths = askopenfilenames(title='Choose images')
        self.add_images(paths)

    def select_taxon_from_photo(self, taxon_id):
        self.inputs.taxon_id_input.text = str(taxon_id)

    def select_observation_from_photo(self, observation_id):
        self.inputs.observation_id_input.text = str(observation_id)

    def remove_image(self, image):
        """ Remove an image from file list and image previews """
        logger.info(f'Main: Removing image {image.metadata_config.image_path}')
        self.file_list.remove(image.metadata_config.image_path)
        image.parent.remove_widget(image)

    def clear(self, *args):
        """ Clear all image selections (selected files, previews, and inputs) """
        logger.info('Main: Clearing image selections')
        self.file_list = []
        self.inputs.observation_id_input.text = ''
        self.inputs.taxon_id_input.text = ''
        self.file_chooser.selection = []
        self.image_previews.clear_widgets()

    @property
    def input_dict(self):
        return {
            "observation_id": int(self.inputs.observation_id_input.text or 0),
            "taxon_id": int(self.inputs.taxon_id_input.text or 0),
            "recursive": self.inputs.recursive_chk.active,
        }

    def get_state(self, *args):
        logger.info(
            'Main:',
            f'IDs: {self.ids}\n' f'Files:\n{self.file_list}\n' f'Input: {self.input_dict}\n',
        )

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return
        # Right-click: Open context menu for the image
        elif touch.button == 'right':
            self.context_menu.show(*get_app().root_window.mouse_pos)
            self.context_menu.ref = instance
            # Enable 'view taxon/observation' menu items, if applicable
            self.context_menu.ids.view_taxon_ctx.disabled = not instance.metadata_config.taxon_id
            self.context_menu.ids.view_observation_ctx.disabled = (
                not instance.metadata_config.observation_id
            )
            self.context_menu.ids.copy_flickr_tags_ctx.disabled = (
                not instance.metadata_config.keyword_meta.flickr_tags
            )
        # Middle-click: remove image
        elif touch.button == 'middle':
            self.remove_image(instance)
        # Left-click: # TODO: larger image view
        else:
            pass

    # TODO: reuse Taxon object previously found by load_image; needs a bit of refactoring
    @staticmethod
    def view_taxon(instance):
        get_app().switch_screen('taxon')
        get_app().select_taxon(id=instance.metadata_config.taxon_id)

    @staticmethod
    def view_metadata(instance):
        get_app().switch_screen('metadata')
        get_app().select_metadata(instance.metadata_config)

    def run(self, *args):
        """ Run image tagging for selected images and input """
        if not self.file_list:
            alert('Select images to tag')
            return
        if not self.input_dict['observation_id'] and not self.input_dict['taxon_id']:
            alert('Select either an observation or an organism to tag images with')
            return
        selected_id = (
            f'Observation ID: {self.input_dict["observation_id"]}'
            if self.input_dict['observation_id']
            else f'Taxon ID: {self.input_dict["taxon_id"]}'
        )
        logger.info(f'Main: Tagging {len(self.file_list)} images with metadata for {selected_id}')

        metadata_settings = get_app().settings_controller.metadata
        # TODO: Handle write errors (like file locked) and show dialog
        all_metadata, _, _ = tag_images(
            self.input_dict['observation_id'],
            self.input_dict['taxon_id'],
            metadata_settings['common_names'],
            metadata_settings['darwin_core'],
            metadata_settings['hierarchical_keywords'],
            metadata_settings['create_xmp'],
            self.file_list,
        )
        alert(f'{len(self.file_list)} images tagged with metadata for {selected_id}')

        # Update image previews with new metadata
        previews = {img.metadata_config.image_path: img for img in self.image_previews.children}
        for metadata in all_metadata:
            previews[metadata.image_path].metadata_config = metadata

    @staticmethod
    def on_taxon_id(input):
        """ Handle entering a taxon ID and pressing Enter """
        get_app().switch_screen('taxon')
        get_app().select_taxon(id=int(input.text))
