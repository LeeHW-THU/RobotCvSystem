import asyncio
import logging
import json
import pathlib

import zmq
import zmq.asyncio

from .executor import Executor

logger = logging.getLogger('zmq_adapter')

class ZmqAdapter:
    def __init__(self, config):
        socket_dir = pathlib.Path(config['command_socket']).parent
        socket_dir.mkdir(parents=True, exist_ok=True)

        ctx = zmq.asyncio.Context.instance()
        self._config = config
        self._command_socket = ctx.socket(zmq.ROUTER)
        self._command_socket.bind('ipc://' + config['command_socket'])
        self._executor = Executor(config)
        self._control_task = None

    async def run(self):
        logger.info('starting listening command')
        while True:
            dealer_id, *msg = await self._command_socket.recv_multipart()
            cmd = msg[0].decode()
            if cmd == 'start':
                if self._control_task is None:
                    logger.info('got start from %s, starting', dealer_id)
                    self._control_task = asyncio.ensure_future(self._executor.run())
                else:
                    logger.info('got start from %s, ignored, already started', dealer_id)

            elif cmd == 'stop':
                if self._control_task is None:
                    logger.info('got stop from %s, ignored, already stopped', dealer_id)
                else:
                    logger.info('got stop from %s, stoping', dealer_id)
                    self._control_task.cancel()
                    try:
                        await self._control_task
                    except asyncio.CancelledError:
                        pass
                    self._control_task = None
            elif cmd == 'turn':
                if self._control_task is None:
                    logger.warning('got turn from %s, unable to turn when stopped', dealer_id)
                elif len(msg) < 2:
                    logger.warning('parameters not provided for turn command')
                else:
                    parameters = json.loads(msg[1])
                    if 'angle' not in parameters:
                        logger.warning('angle not provided for turn command')
                    else:
                        self._executor.controller.turn(parameters['angle'])
            else:
                logger.warning('got invalid command %s from %s', cmd, dealer_id)
