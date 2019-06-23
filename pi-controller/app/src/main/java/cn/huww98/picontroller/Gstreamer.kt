package cn.huww98.picontroller

import android.content.Context
import android.util.Log
import android.view.SurfaceHolder
import kotlin.coroutines.Continuation
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

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

    private external fun nativeInit()      // Initialize native code
    private external fun nativeStart(remoteAddress: String)      // build pipeline, etc
    private external fun nativeFinalize()  // Destroy pipeline and shutdown native code
    private external fun nativeSurfaceInit(surface: Any)
    private external fun nativeSurfaceFinalize()
    private external fun nativeGetPort(): Int
    private val native_custom_data: Long = 0      // Native code will use this to keep private data

    init {
        org.freedesktop.gstreamer.GStreamer.init(context)
        nativeInit()
    }

    private var started = false;
    private var startContinuation: Continuation<Unit>? = null;
    suspend fun start(remoteAddress: String) = suspendCoroutine<Unit> { continuation ->
        if (started) throw IllegalStateException("Already started")
        this.started = true
        this.startContinuation = continuation
        nativeStart(remoteAddress)
    }

    // Called from native code. This sets the content of the TextView from the UI thread.
    private fun setMessage(message: String) {
        Log.d("GStreamer", message)
//        Toast.makeText(context, message, Toast.LENGTH_LONG).show()
    }

    private fun onGStreamerInitialized() {
        Log.i("GStreamer", "Started.")
        startContinuation!!.resume(Unit)
    }

    fun surfaceChanged(holder: SurfaceHolder) {
        nativeSurfaceInit(holder.surface)
    }

    fun surfaceDestroyed() {
        nativeSurfaceFinalize()
    }

    fun getPort(): Int {
        val port = nativeGetPort();
        if (port <= 0)
            throw RuntimeException("Got invalid port number from native: $port")
        return port;
    }

    fun finalize() {
        nativeFinalize()
    }
}
