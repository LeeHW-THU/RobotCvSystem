import asyncio
import json
import logging
from typing import Iterator, Optional

from .motor import Motor
from .videotransmitter import VideoTransmitter

logger = logging.getLogger('Controller')

class Controller:
    PORT = 7728

    def __init__(self, on_begin=None, on_end=None):
        self.left_motor = Motor(1, 4)
        self.right_motor = Motor(5, 6)
        self.on_begin = on_begin
        self.on_end = on_end

        self.connection_task = None
        self.remote_addr = None
        self.video_transmitter = None

    async def start_server(self):
        async def on_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            logger.info('Connected from %s', self.remote_addr)
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
            writer.write_eof()
            self.end_control()
            self.connection_task = None

        def run_on_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            if self.connection_task is not None:
                logger.warning('Trying to connect, but controller already connected.')
                writer.write('Already connected'.encode())
                writer.write_eof()
                return
            self.remote_addr = writer.transport.get_extra_info('peername')
            self.connection_task = asyncio.ensure_future(on_connected(reader, writer))

        await asyncio.start_server(run_on_connected, port=self.PORT)

    def _motors(self) -> Iterator[Motor]:
        yield self.left_motor
        yield self.right_motor

    def _process_command(self, cmd):
        logger.debug('command received: %s', cmd)
        try:
            cmd = json.loads(cmd)
        except json.JSONDecodeError:
            logger.warning('Invalid json command: %s', cmd)
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
            if 'video' in cmd:
                video = cmd['video']
                if self.video_transmitter is not None:
                    logger.warning('video command can only be send once')
                elif 'port' not in video:
                    logger.warning('video command should specify "port" to transmit to')
                else:
                    self.video_transmitter = VideoTransmitter(self.remote_addr[0], video['port'])
        else:
            logger.warning('Unsupported command type %s', type(cmd))

    def stop(self):
        """Stop all motion
        """
        for m in self._motors():
            m.input(0)

    def begin_control(self):
        for m in self._motors():
            m.start()
        if self.on_begin:
            self.on_begin()

    def end_control(self):
        self.stop()
        for m in self._motors():
            m.stop()
        if self.video_transmitter is not None:
            self.video_transmitter.stop()
            self.video_transmitter = None
        if self.on_end:
            self.on_end()
