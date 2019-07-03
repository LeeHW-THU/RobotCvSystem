import logging
import asyncio
import pathlib

import zmq
import zmq.asyncio

from .camera import Camera

logger = logging.getLogger('VideoTransmitter')

class VideoTransmitter:
    def __init__(self, config: dict, zmq_context=None):
        self.zmq_ctx = zmq_context or zmq.asyncio.Context.instance()
        self._config = config

        socket_dir = pathlib.Path(config['data_socket']).parent
        socket_dir.mkdir(parents=True, exist_ok=True)

        self.data_socket = self.zmq_ctx.socket(zmq.PUB)
        self.data_socket.set_hwm(3)
        self.data_socket.bind('ipc://' + config['data_socket'])
        self.data_task = None

    async def run(self):
        await self.command()

    async def command(self):
        cmd_socket = self.zmq_ctx.socket(zmq.ROUTER)
        cmd_socket.bind('ipc://' + self._config['command_socket'])
        while True:
            dealer_id, *msg = await cmd_socket.recv_multipart()
            cmd = msg[0].decode()
            if cmd == 'start':
                if self.data_task is None:
                    logger.info('got start from %s, starting', dealer_id)
                    self.data_task = asyncio.ensure_future(self.data())
                else:
                    logger.info('got start from %s, ignored, already started', dealer_id)

            elif cmd == 'stop':
                if self.data_task is None:
                    logger.info('got stop from %s, ignored, already stopped', dealer_id)
                else:
                    logger.info('got stop from %s, stoping', dealer_id)
                    self.data_task.cancel()
                    try:
                        await self.data_task
                    except asyncio.CancelledError:
                        pass
                    self.data_task = None
            else:
                logger.warning('got invalid command %s from %s', cmd, dealer_id)

    async def data(self):
        async with Camera(self._config['camera']) as camera:
            while True:
                data = await camera.get_frame()
                self.data_socket.send(data, copy=False)
                logger.debug('data sent')
