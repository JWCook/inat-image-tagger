import asyncio

from kivymd.uix.progressbar import MDProgressBar

from naturtag.controllers.batch_loader import BatchLoader


class SleepyBatchLoader(BatchLoader):
    """ BatchLoader for testing that just sleeps """

    def __init__(self, **kwargs):
        super().__init__(worker_callback=self.yawn, **kwargs)

    async def yawn(self, item, **kwargs):
        print(kwargs)
        await asyncio.sleep(item)
        await self.increment_progress()


async def test_loader(self):
    self.progress_bar = MDProgressBar(max=1000)
    self.status_bar.add_widget(self.progress_bar)
    loader = SleepyBatchLoader()

    def update_progress(obj, value):
        print(value)
        self.progress_bar.value = value

    def load_complete(*args):
        self.progress_bar.color = 0.1, 0.8, 0.1, 1

    loader.bind(on_progress=update_progress)
    loader.bind(on_complete=load_complete)
    loader.bind(on_load=lambda *x: print('Loaded', x))

    await loader.add_batch((0.012 for _ in range(250)), key='batch 1')
    await loader.add_batch((0.014 for _ in range(250)), key='batch 2')
    await loader.add_batch((0.016 for _ in range(250)), key='batch 3')
    await loader.add_batch((0.018 for _ in range(250)), key='batch 4')


asyncio.run(test_loader())
