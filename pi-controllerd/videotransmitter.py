import os
import subprocess
import signal
import logging
import threading

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

logger = logging.getLogger('video-transmitter')

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logger.error("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True


class VideoTransmitter:
    run_base = '/run/pi-controllerd'
    h264_fifo = os.path.join(run_base, 'h264video.fifo')

    def __init__(self, host: str, port: int, rtcp_local_port=7729,
                 width=1296, height=972, framerate=30, bitrate=1000000):
        if not os.path.exists(self.run_base):
            raise RuntimeError('Path {} not exist, this should be provided by systemd. If you start program manually, please mkdir and chown.'.format(self.run_base))
        if not os.path.exists(self.h264_fifo):
            os.mkfifo(self.h264_fifo)

        self.raspivid_process = subprocess.Popen(
            ['raspivid', '--timeout', '0', '--width', str(width), '--height', str(height),
             '--framerate', str(framerate), '--intra', '60', '--bitrate', str(bitrate), '--flush', '--output', self.h264_fifo],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        Gst.init(None)
        pipeline_def = "rtpbin name=rtpbin \
    filesrc location={} do-timestamp=true ! queue leaky=downstream max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 ! rtprtxqueue ! rtpbin.send_rtp_sink_0 \
    rtpbin.send_rtp_src_0 ! udpsink host={} port={} sync=false \
    udpsrc port={} ! rtpbin.recv_rtcp_sink_0".format(self.h264_fifo, host, port, rtcp_local_port)
        # Here leaky queue is used to discard buffers when downstream is blocked, i.e. udpsink cannot transmit fast enough
        # This way we always transmitting latest content
        # filesrc do-timestamp=true is needed for rtph264pay to add correct timestamp in RTP package
        pipeline = Gst.parse_launch(pipeline_def)
        self.loop = GObject.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect ("message", bus_call, self.loop)

        # start play back and listed to events
        pipeline.set_state(Gst.State.PLAYING)

        def mainloop():
            logger.info('Starting transmition to {}:{}, listen for RTCP at port {}'.format(host, port, rtcp_local_port))
            try:
                self.loop.run()
            except Exception as e:
                logger.error("Error in main loop", exec_info=True)
            logger.info('Stopped transmition')
            # cleanup
            pipeline.set_state(Gst.State.NULL)

        thread = threading.Thread(target=mainloop)
        thread.daemon = True
        thread.start()
        self.gstreamer_thread = thread

    def stop(self):
        """Stop transmition.

        To start again, create a new instance
        """
        self.raspivid_process.terminate()
        self.raspivid_process.wait()
        self.loop.quit()
        self.gstreamer_thread.join()

if __name__ == "__main__":
    # Main for test
    logging.basicConfig(level=logging.INFO)

    transmitter = VideoTransmitter('192.168.137.1', 5000)
    input('Press Enter to stop')
    transmitter.stop()
