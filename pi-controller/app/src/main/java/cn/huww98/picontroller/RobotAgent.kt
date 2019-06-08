package cn.huww98.picontroller

import android.util.Log
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

    init {
        val socket = Socket(connectionInfo.address, PORT)
        writer = OutputStreamWriter(socket.getOutputStream(), Charsets.UTF_8)
        Log.i(TAG, "connected to ${connectionInfo.address.hostAddress}:$PORT")
    }

    fun command(cmd: IControlCommand) {
        objectMapper.writeValue(writer, cmd)
        writer.write("\n")
        writer.flush()
    }

    fun command(cmd: Observable<IControlCommand>): Completable {
        return cmd.throttleLatest(100, TimeUnit.MILLISECONDS)
            .distinctUntilChanged()
            .observeOn(Schedulers.io())
            .doOnNext { command(it) }
            .ignoreElements()
    }

    fun close() {
        Log.d(TAG, "closing")
        writer.close()
    }
}
