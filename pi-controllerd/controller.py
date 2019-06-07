import asyncio
import json
import logging
from typing import Iterator

from .motor import Motor

logger = logging.getLogger('Controller')

class Controller:
    PORT = 7728

    def __init__(self, on_begin=None, on_end=None):
        self.left_motor = Motor(1, 4)
        self.right_motor = Motor(5, 6)
        self.on_begin = on_begin
        self.on_end = on_end
        self.connected = False

    async def start_server(self):
        async def on_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            if self.connected:
                logger.warning('Tring to connect, but controller already connected.'.encode())
                writer.write('Already connected'.encode())
                writer.write_eof()
                return

            logger.info('Connected')
            self.begin_control()

            while not reader.at_eof():
                line = await reader.readline()
                line = line.decode().strip()
                if not line:
                    if not reader.at_eof():
                        logger.warning('Empty command received')
                    continue
                self._process_command(line)

            logger.info('Disonnected')
            self.end_control()

        await asyncio.start_server(on_connected, port=self.PORT)

    def _motors(self) -> Iterator[Motor]:
        yield self.left_motor
        yield self.right_motor

    def _process_command(self, cmd):
        logger.debug('command received: %s', cmd)
        try:
            cmd = json.loads(cmd)
        except json.JSONDecodeError:
            logger.warning('Invalid json command')
            return

        if isinstance(cmd, str):
            if cmd == 'Stop':
                self.stop()
            else:
                logger.warning('Unknown command %s', cmd)
        elif isinstance(cmd, dict):
            if 'power' in cmd:
                power = cmd['power']
                if 'left' in power:
                    self.left_motor.input(power['left'])
                if 'right' in power:
                    self.right_motor.input(power['right'])
        else:
            logger.warning('Unsupported command type %s', type(cmd))

    def stop(self):
        for m in self._motors():
            m.input(0)

    def begin_control(self):
        self.connected = True
        for m in self._motors():
            m.start()
        if self.on_begin:
            self.on_begin()

    def end_control(self):
        self.stop()
        self.connected = False
        for m in self._motors():
            m.stop()
        if self.on_end:
            self.on_end()


class RobotControlProtocol(asyncio.Protocol):
    def __init__(self, controller: Controller):
        self.controller = controller
        self.transport = None

    def connection_made(self, transport):
        if self.controller.connected:
            transport.write('Already connected'.encode())
            transport.close()
        else:
            self.transport = transport

    def data_received(self, data):
        if self.transport is None:
            return
        message = data.decode()
        print('Data received: {!r}'.format(message))

        print('Send: {!r}'.format(message))
        self.transport.write(data)

        print('Close the client socket')
        self.transport.close()
