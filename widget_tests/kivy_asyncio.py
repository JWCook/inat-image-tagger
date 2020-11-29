"""
Kivy asyncio example app.
From: https://gist.github.com/dolang/42df81c78bf0108209d837f6ba9da052

Kivy needs to run on the main thread and its graphical instructions have to be
called from there.  But it's still possible to run an asyncio EventLoop, it
just has to happen on its own, separate thread.

Requires Python 3.5+.
"""
import os

# Set GL backend before any kivy modules are imported
os.environ['KIVY_GL_BACKEND'] = 'sdl2'
import asyncio
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

KV = '''\
<RootLayout>:
    orientation: 'vertical'
    Button:
        id: btn
        text: 'Start EventLoop thread.'
        on_press: app.start_event_loop_thread()
    TextInput:
        multiline: False
        size_hint_y: 0.25
        on_text: app.submit_pulse_text(args[1])
    BoxLayout:
        Label:
            id: pulse_listener  
'''


class RootLayout(BoxLayout):
    pass


class EventLoopWorker(EventDispatcher):

    __events__ = ('on_pulse',)  # defines this EventDispatcher's sole event

    def __init__(self):
        super().__init__()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self.loop = None
        # the following are for the pulse() coroutine, see below
        self._default_pulse = ['tick!', 'tock!']
        self._pulse = None
        self._pulse_task = None
        self.dispatch = mainthread(self.dispatch)

    def start(self):
        self._thread.start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.set_pulse_text('')
        self.loop.run_forever()

    async def pulse(self):
        """Core coroutine of this asyncio event loop. Repeats a pulse message in a short interval
        by dispatching a Kivy event `on_pulse` with the help of `@mainthread`
        """

        def _pulse_messages():
            while True:
                yield from self._pulse or self._default_pulse

        for msg in _pulse_messages():
            print(msg)
            self.dispatch('on_pulse', msg)  # Left label: event
            await asyncio.sleep(1)

    def set_pulse_text(self, text):
        self._pulse = str(text or '').strip().split()
        if self._pulse_task is not None:
            self._pulse_task.cancel()
        self._pulse_task = self.loop.create_task(self.pulse())

    def submit(self, text):
        self.loop.call_soon_threadsafe(self.set_pulse_text, text)

    def on_pulse(self, *_):
        pass


class AsyncioExampleApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_loop_worker = None

    def build(self):
        return RootLayout()

    def start_event_loop_thread(self):
        """Start the asyncio event loop thread. Bound to the top button."""
        if self.event_loop_worker is not None:
            return
        self.root.ids.btn.text = (
            "Running the asyncio EventLoop now...\n\n\n\nNow enter a few words below."
        )
        self.event_loop_worker = EventLoopWorker()
        # make the label react to the worker's `on_pulse` event:
        self.event_loop_worker.bind(
            on_pulse=lambda x, text: setattr(self.root.ids.pulse_listener, 'text', text)
        )
        self.event_loop_worker.start()

    def submit_pulse_text(self, text):
        """Send the TextInput string over to the asyncio event loop worker.
        use the thread safe variant to run it on the asyncio event loop:
        """
        if self.event_loop_worker is not None:
            self.event_loop_worker.submit(text)


if __name__ == '__main__':
    Builder.load_string(KV)
    AsyncioExampleApp().run()
