package cn.huww98.picontroller

import android.content.Context
import android.util.Log
import android.view.SurfaceHolder

class Gstreamer(val context: Context) {
    companion object {
        init {
            System.loadLibrary("gstreamer_android")
            System.loadLibrary("video-transmission")
            nativeClassInit()
        }

        @JvmStatic
        private external fun nativeClassInit(): Boolean  // Initialize native class: cache Method IDs for callbacks
    }

    private external fun nativeInit()      // Initialize native code, build pipeline, etc
    private external fun nativeFinalize()  // Destroy pipeline and shutdown native code
    private external fun nativePlay()      // Set pipeline to PLAYING
    private external fun nativePause()     // Set pipeline to PAUSED
    private external fun nativeSurfaceInit(surface: Any)
    private external fun nativeSurfaceFinalize()
    private val native_custom_data: Long = 0      // Native code will use this to keep private data

    init {
        org.freedesktop.gstreamer.GStreamer.init(context)
        nativeInit()
    }

    // Called from native code. This sets the content of the TextView from the UI thread.
    private fun setMessage(message: String) {
        Log.d("GStreamer", message)
//        Toast.makeText(context, message, Toast.LENGTH_LONG).show()
    }

    private fun onGStreamerInitialized() {
        nativePlay()
    }

    fun surfaceChanged(holder: SurfaceHolder) {
        nativeSurfaceInit(holder.surface)
    }

    fun surfaceDestroyed() {
        nativeSurfaceFinalize()
    }
}
