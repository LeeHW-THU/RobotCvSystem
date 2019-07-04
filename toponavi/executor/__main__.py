import pathlib
import asyncio
import logging

import yaml
import wiringpi

from .zmqadapter import ZmqAdapter

async def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)

    zmq_adapter = ZmqAdapter(config)
    await zmq_adapter.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
