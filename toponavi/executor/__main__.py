import pathlib
import asyncio
import logging
import signal
import logging

import yaml
import wiringpi
from systemd import journal

from .zmqadapter import ZmqAdapter

async def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)

    with ZmqAdapter(config) as zmq_adapter:
        run_task = asyncio.ensure_future(zmq_adapter.run())
        signal.signal(signal.SIGTERM, lambda *args: run_task.cancel())
        await run_task

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.root.addHandler(journal.JournalHandler())

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except asyncio.CancelledError:
        pass
    logging.debug("main ended")
