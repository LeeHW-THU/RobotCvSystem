import asyncio
import pathlib

import yaml

from .videotransmitter import VideoTransmitter

async def main():
    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)
    transmitter = VideoTransmitter(config)
    await transmitter.run()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
