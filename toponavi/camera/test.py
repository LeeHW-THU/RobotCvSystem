import multiprocessing
import pathlib
import logging
import asyncio
import time

import zmq
import yaml

from .__main__ import main as server_main

logger = logging.getLogger('camera-test')

def server():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server_main())

def main():
    server_process = multiprocessing.Process(target=server)
    server_process.start()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)
    ctx = zmq.Context()
    cmd_socket = ctx.socket(zmq.DEALER)
    cmd_socket.connect('ipc://' + config['command_socket'])
    data_socket = ctx.socket(zmq.SUB)
    data_socket.setsockopt(zmq.SUBSCRIBE, b'')
    data_socket.connect('ipc://' + config['data_socket'])

    def test(message_count):
        cmd_socket.send_string('start')
        logger.info('start sent')
        for i in range(message_count):
            data = data_socket.recv(copy=False)
            logger.info('#%d message recieved, len %d', i, len(data.bytes))
        cmd_socket.send_string('stop')
        logger.info('stop sent')

    test(300)
    time.sleep(2)
    test(30)

    print('Test complete, press Ctrl+C to stop')
    server_process.join() # server_process should not stop

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        level=logging.DEBUG)
    main()
