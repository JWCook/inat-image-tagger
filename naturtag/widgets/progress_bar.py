from logging import getLogger

from kivy.animation import Animation
from kivymd.uix.progressbar import MDProgressBar

FINISHED_COLOR = 0.1, 0.8, 0.1, 1
REMOVED_COLOR = 0, 0, 0, 0
logger = getLogger().getChild(__name__)


class LoaderProgressBar(MDProgressBar):
    """ A progress bar with some extra features to sync with a BatchLoader """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_color = self.color
        self.event = None
        self.loader = None

    def start(self, max=100, loader=None):
        """ (Re)start the progress bar, and bind a BatchLoader's progress update events to it """
        self.cancel()
        self.value = 0
        self.max = max
        self.color = self.start_color
        self.loader = loader

        # Bind a BatchLoader's progress update events
        if self.loader:
            self.loader.bind(on_progress=self.update)
            self.loader.bind(on_complete=self.finish)

    def update(self, obj, value):
        """ Update progress value (for simpler event binding/unbinding) """
        self.value = value

    def cancel(self):
        """ Cancel any currently running animation and unbind loader events """
        logger.debug(f'Progress canceled at {self.value}/{self.max}')
        if self.loader:
            self.loader.unbind(on_progress=self.update)
            self.loader.unbind(on_complete=self.finish)
        if self.event:
            self.event.cancel_all(self)
            self.event = None

    def finish(self, *args):
        """ Finish the progress by changing color w/ animation and unbinding events """
        self.cancel()
        self.value = self.max
        self.color = FINISHED_COLOR
        self.event = Animation(color=REMOVED_COLOR, duration=3, t='out_expo')
        self.event.start(self)
