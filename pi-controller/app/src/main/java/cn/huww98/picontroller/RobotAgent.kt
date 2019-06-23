package cn.huww98.picontroller

import android.util.Log
import com.fasterxml.jackson.annotation.JsonTypeInfo
import com.fasterxml.jackson.annotation.JsonTypeName
import com.fasterxml.jackson.core.JsonGenerator
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import io.reactivex.Completable
import io.reactivex.Observable
import io.reactivex.schedulers.Schedulers
import java.io.OutputStreamWriter
import java.net.Socket
import java.util.concurrent.TimeUnit

class RobotAgent(connectionInfo: RobotConnectionInfo) {
    companion object {
        const val PORT = 7728
        const val TAG = "Robot-Agent"
    }

    private val writer: OutputStreamWriter
    private val objectMapper = jacksonObjectMapper()
        .disable(JsonGenerator.Feature.AUTO_CLOSE_TARGET)
        .disable(JsonGenerator.Feature.FLUSH_PASSED_TO_STREAM)

    init {
        val socket = Socket(connectionInfo.address, PORT, connectionInfo.localAddress, 0)
        writer = OutputStreamWriter(socket.getOutputStream(), Charsets.UTF_8)
        Log.i(TAG, "connected to ${connectionInfo.address.hostAddress}:$PORT")
    }

    private fun sendCommand(cmd: Any) {
        objectMapper.writeValue(writer, cmd)
        writer.write("\n")
        writer.flush()
    }

    fun command(cmd: Observable<IControlCommand>): Completable {
        return cmd.throttleLatest(100, TimeUnit.MILLISECONDS)
            .distinctUntilChanged()
            .observeOn(Schedulers.io())
            .doOnNext { sendCommand(it) }
            .ignoreElements()
    }

    fun video(port: Int) {
        @JsonTypeName("video")
        @JsonTypeInfo(include = JsonTypeInfo.As.WRAPPER_OBJECT, use = JsonTypeInfo.Id.NAME)
        data class VideoCommand(val port: Int)

        sendCommand(VideoCommand(port))
    }

    fun close() {
        Log.d(TAG, "closing")
        writer.close()
    }
}
