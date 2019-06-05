import asyncio
import json
from typing import Iterator

from .motor import Motor

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
                writer.write('Already connected')
                writer.write_eof()
                return
            self.begin_control()
            while not reader.at_eof():
                line = await reader.readline()
                self._process_command(line.decode().trim())
            self.end_control()

        await asyncio.start_server(on_connected, port=self.PORT)

    def _motors(self) -> Iterator[Motor]:
        yield self.left_motor
        yield self.right_motor

    def _process_command(self, cmd):
        cmd = json.loads(cmd)
        if 'power' in cmd:
            power = cmd['power']
            if 'left' in power:
                self.left_motor.input(power['left'])
            if 'right' in power:
                self.right_motor.input(power['right'])

    def begin_control(self):
        self.connected = True
        for m in self._motors():
            m.start()
        if self.on_begin:
            self.on_begin()

    def end_control(self):
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
