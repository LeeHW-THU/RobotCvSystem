package cn.huww98.picontroller

import android.content.Context

class Gstreamer {
    companion object {
        init {
            System.loadLibrary("gstreamer_android")
            System.loadLibrary("video-transmission")
        }
    }

    private external fun nativeGetGStreamerInfo(): String
    fun init(context: Context) {
        org.freedesktop.gstreamer.GStreamer.init(context)
    }

    fun version() = nativeGetGStreamerInfo()
}
