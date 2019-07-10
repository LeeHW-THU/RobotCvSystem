import pathlib
import logging
import threading

import yaml
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

logger = logging.getLogger('gstreamer-transmitter')

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logger.error("Error: %s: %s\n", err, debug)
        loop.quit()
    return True


class GstreamerTransmitter:
    def __init__(self, h264_fifo, config):
        logger.debug('gstreamer init')
        Gst.init(None)
        pipeline_def = "rtpbin name=rtpbin \
    filesrc location={} do-timestamp=true ! queue leaky=downstream max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 ! rtprtxqueue ! rtpbin.send_rtp_sink_0 \
    rtpbin.send_rtp_src_0 ! udpsink host={} port={} sync=false \
    udpsrc port={} ! rtpbin.recv_rtcp_sink_0".format(h264_fifo, config['host'], config['port'], config['rtcp_local_port'])
        # Here leaky queue is used to discard buffers when downstream is blocked, i.e. udpsink cannot transmit fast enough
        # This way we always transmitting latest content
        # filesrc do-timestamp=true is needed for rtph264pay to add correct timestamp in RTP package
        pipeline = Gst.parse_launch(pipeline_def)
        self.loop = GObject.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, self.loop)

        # start play back and listed to events
        pipeline.set_state(Gst.State.PLAYING)

        def mainloop():
            logger.info('Starting transmition to %s:%d, listen for RTCP at port %d', config['host'], config['port'], config['rtcp_local_port'])
            try:
                self.loop.run()
            except Exception:
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
        self.loop.quit()
        self.gstreamer_thread.join()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()
