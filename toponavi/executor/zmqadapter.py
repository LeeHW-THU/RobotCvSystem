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

        self._ctx = zmq.asyncio.Context.instance()
        self._config = config
        self._command_socket = self._ctx.socket(zmq.ROUTER)
        self._command_socket.bind('ipc://' + config['command_socket'])
        self._executor = Executor(config)
        self._control_task = None

    def _start_control(self):
        if self.control_started:
            return
        self._control_task = asyncio.ensure_future(self._executor.run())

    async def _stop_control(self):
        if not self.control_started:
            return
        control_task = self._control_task
        self._control_task = None

        control_task.cancel()
        try:
            await control_task
        except asyncio.CancelledError:
            pass
        logger.debug('control stopped')

    @property
    def control_started(self):
        return self._control_task is not None

    async def command(self):
        logger.info('starting listening command')
        while True:
            dealer_id, *msg = await self._command_socket.recv_multipart()
            cmd = msg[0].decode()
            if cmd == 'start':
                if self.control_started:
                    logger.info('got start from %s, ignored, already started', dealer_id)
                else:
                    logger.info('got start from %s, starting', dealer_id)
                    self._start_control()

            elif cmd == 'stop':
                if not self.control_started:
                    logger.info('got stop from %s, ignored, already stopped', dealer_id)
                else:
                    logger.info('got stop from %s, stoping', dealer_id)
                    self._stop_control()
            elif cmd == 'turn':
                if len(msg) < 2:
                    logger.warning('parameters not provided for turn command')
                else:
                    parameters = json.loads(msg[1].decode())
                    if 'angle' not in parameters:
                        logger.warning('angle not provided for turn command')
                    else:
                        angle = parameters['angle']
                        logger.info('got turn from %s, angle %.3f', dealer_id, angle)
                        self._start_control()
                        self._executor.controller.turn(angle)
            elif cmd == 'scan':
                logger.info('got scan from %s.', dealer_id)
                self._start_control()
                self._executor.controller.scan()
            else:
                logger.warning('got invalid command %s from %s', cmd, dealer_id)

    async def run(self):
        try:
            await self.command()
        finally:
            await self._stop_control()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        logger.debug('disposing')
        self._command_socket.close()
        self._ctx.term()
        logger.debug('disposed')
