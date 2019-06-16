package cn.huww98.picontroller

import android.content.Context
import android.hardware.SensorManager
import android.os.Bundle
import android.support.v7.app.AppCompatActivity
import android.util.Log
import android.view.MotionEvent
import android.view.View
import android.view.View.INVISIBLE
import android.view.View.VISIBLE
import android.widget.TextView
import io.reactivex.Observable
import io.reactivex.Single
import io.reactivex.android.schedulers.AndroidSchedulers
import io.reactivex.disposables.CompositeDisposable
import io.reactivex.disposables.Disposable
import io.reactivex.rxkotlin.ofType
import io.reactivex.rxkotlin.subscribeBy
import io.reactivex.schedulers.Schedulers
import io.reactivex.subjects.BehaviorSubject
import io.reactivex.subjects.PublishSubject
import io.reactivex.subjects.Subject
import kotlinx.android.synthetic.main.activity_fullscreen.*

class FullscreenActivity : AppCompatActivity() {

    private var connectionInfoSubscribe: Disposable? = null

    private fun startDiscovery() {
        val discovery = RobotDiscovery(this)
        runOnUiThread {
            discoveringPrompt.visibility = VISIBLE
        }
        connectionInfoSubscribe = discovery.discover()
            .firstElement()
            .subscribe {
                stopDiscovery()
                beginControl(it)
            }
    }

    private fun stopDiscovery() {
        connectionInfoSubscribe?.dispose()
        connectionInfoSubscribe = null
        runOnUiThread {
            discoveringPrompt.visibility = INVISIBLE
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val gstreamer = Gstreamer()
        gstreamer.init(this)
        Log.d("gst-test", gstreamer.version())

        setContentView(R.layout.activity_fullscreen)

        startDiscovery()

        stopButton.setOnClickListener {
            controlSession?.stop()
        }
    }

    private fun Observable<Double>.subscribeOnTextView(txt: TextView): Disposable {
        return this.map { "%.2f".format(it) }
            .observeOn(AndroidSchedulers.mainThread())
            .doOnDispose { runOnUiThread { txt.text = "" } }
            .subscribe { txt.text = it }
    }

    private fun Observable<Boolean>.subscribeOnViewVisibility(view: View): Disposable {
        return this.map { if (it) VISIBLE else INVISIBLE }
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe { view.visibility = it }
    }

    private val dy = PublishSubject.create<Float>()

    inner class ControlSession(connectionInfo: RobotConnectionInfo) {
        private val controlSubscribes: CompositeDisposable
        private var robot: RobotAgent? = null
        private val speedController = ScreenSpeedController(dy)
        private val stoppedSubject: Subject<Boolean>

        init {
            stoppedSubject = BehaviorSubject.createDefault(true)

            val controller = DifferentialController(
                speedController,
                AccelerometerTurnController(getSystemService(Context.SENSOR_SERVICE) as SensorManager),
                stoppedSubject
            )

            val ignore = Single.fromCallable { RobotAgent(connectionInfo) }
                .subscribeOn(Schedulers.io())
                .subscribe { newRobot ->
                    newRobot.command(controller.command)
                        .subscribeBy(onError = {
                            if (!disposing) {
                                Log.w("Main", "Error, restart discovery", it)
                                endControl()
                                startDiscovery()
                            }
                        })
                    robot = newRobot
                    runOnUiThread { controlSessionOverlay.visibility = VISIBLE }
                }

            val powerCommands = controller.command.ofType<PowerCommand>()

            controlSubscribes = CompositeDisposable(
                controller.speed.subscribeOnTextView(speedTxt),
                controller.turn.subscribeOnTextView(turnTxt),
                powerCommands.map { it.left }.subscribeOnTextView(leftTxt),
                powerCommands.map { it.right }.subscribeOnTextView(rightTxt),
                stoppedSubject.subscribeOnViewVisibility(stoppedPrompt),
                stoppedSubject.map { !it }.subscribeOnViewVisibility(motorInfoGroup)
            )
        }

        private var disposing = false
        fun dispose() {
            disposing = true
            controlSubscribes.dispose()
            robot?.close() // TODO: Robot not created yet?
        }

        fun stop() {
            speedController.reset()
            stoppedSubject.onNext(true)
        }

        fun resume() {
            stoppedSubject.onNext(false)
        }
    }

    private var controlSession: ControlSession? = null

    private fun beginControl(connectionInfo: RobotConnectionInfo) {
        runOnUiThread {
            connectionInfoTxt.apply {
                text = connectionInfo.address.hostAddress
                visibility = VISIBLE
            }
        }

        controlSession = ControlSession(connectionInfo)
    }

    private fun endControl() {
        runOnUiThread {
            connectionInfoTxt.visibility = INVISIBLE
            controlSessionOverlay.visibility = INVISIBLE
        }
        controlSession?.dispose()
    }

    private var lastY = 0.0f

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val y = event.y
        when (event.action) {
            MotionEvent.ACTION_MOVE -> dy.onNext(y - lastY)
        }
        lastY = y

        controlSession?.resume()
        return true
    }

    override fun onDestroy() {
        super.onDestroy()
        stopDiscovery()
        endControl()
    }
}
