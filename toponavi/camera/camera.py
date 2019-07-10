import asyncio
import logging
import pathlib
import os

logger = logging.getLogger('camera')

class Camera:
    def __init__(self, h264_fifo, config):
        self._config = config
        self.h264_fifo = h264_fifo
        self.raspivid_process = None
        self.opened = False

    async def open(self):
        if self.opened:
            return

        self.opened = True
        cfg = self._config
        h264_fifo = pathlib.Path(self.h264_fifo)
        if not h264_fifo.exists():
            os.mkfifo(str(h264_fifo))
        try:
            logger.debug('starting raspivid')
            self.raspivid_process = await asyncio.create_subprocess_exec(
                'raspivid', '--timeout', '0', '--width', str(cfg['width']), '--height', str(cfg['height']),
                '--framerate', str(cfg['framerate']), '--raw', '-', '--output', str(h264_fifo), '--flush',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        except:
            logger.error('error while start raspivid', exc_info=True)
            raise

    async def __aenter__(self):
        await self.open()
        return self

    async def get_frame(self):
        if self.raspivid_process is None:
            raise RuntimeError('Use "async with"')
        data = await self.raspivid_process.stdout.readexactly(self._config['frame_size'])
        return data

    async def dispose(self):
        if not self.opened:
            return
        self.opened = False

        self.raspivid_process.terminate()
        await self.raspivid_process.wait()

    async def __aexit__(self, *args):
        await self.dispose()
