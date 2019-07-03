import asyncio
import logging

logger = logging.getLogger('camera')

class Camera:
    def __init__(self, config):
        self._config = config
        self.raspivid_process = None
        self.opened = False

    async def open(self):
        if self.opened:
            raise RuntimeError('already opened')

        self.opened = True
        cfg = self._config
        try:
            self.raspivid_process = await asyncio.create_subprocess_exec(
                'raspividyuv', '--timeout', '0', '--width', str(cfg['width']), '--height', str(cfg['height']),
                '--framerate', str(cfg['framerate']), '--output', '-',
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
