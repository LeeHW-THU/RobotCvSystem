package cn.huww98.picontroller

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import io.reactivex.Observable
import io.reactivex.rxkotlin.Observables
import io.reactivex.subjects.BehaviorSubject
import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.max
import kotlin.math.min

interface ITurnController {
    /**
     * 绝对值1表示最大旋转速度，左转为正，右转为负
     */
    val turn: Observable<Double>
}

interface ISpeedController {
    /**
     * 绝对值1表示全速，前进为正，后退为负
     */
    val speed: Observable<Double>
}

class AccelerometerTurnController(val sensorManager: SensorManager) : ITurnController {
    companion object {
        const val SCALE_FACTOR = 1.0 / PI
    }

    private fun sensorData(): Observable<FloatArray> {
        return Observable.create<FloatArray> { emitter ->
            val sensor = sensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY)

            val listener = object : SensorEventListener {
                override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
                override fun onSensorChanged(event: SensorEvent) {
                    if (event.sensor.type != Sensor.TYPE_GRAVITY)
                        return
                    emitter.onNext(event.values)
                }
            }
            sensorManager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_GAME)
            emitter.setCancellable { sensorManager.unregisterListener(listener) }
        }
    }

    override val turn: Observable<Double> = sensorData().map {
        SCALE_FACTOR * atan2(-it[1], it[0])
    }
}

class ScreenSpeedController(dy: Observable<Float>) : ISpeedController {
    companion object {
        const val ZERO_MARGIN = 0.2
        const val MAX_SPEED = 1.0
        const val RANGE = 2 * MAX_SPEED + ZERO_MARGIN
        const val INITIAL = MAX_SPEED + ZERO_MARGIN

        const val SCALE_FACTOR = -1.0 / 400.0
    }

    private val slideValueSubject = BehaviorSubject.createDefault(INITIAL)
    private var lastSlideValue = INITIAL
    @Synchronized
    private fun updateSlideValue(d: Double) {
        synchronized(lastSlideValue) {
            lastSlideValue = min(RANGE, max(0.0, lastSlideValue + d))
            slideValueSubject.onNext(lastSlideValue)
        }
    }

    fun reset() {
        synchronized(lastSlideValue) {
            lastSlideValue = INITIAL
            slideValueSubject.onNext(lastSlideValue)
        }
    }

    private val dySubscribe = dy.map { it * SCALE_FACTOR }
        .subscribe(this::updateSlideValue)

    override val speed: Observable<Double> = slideValueSubject
        .map {
            when {
                it < MAX_SPEED -> it - MAX_SPEED
                it > MAX_SPEED + ZERO_MARGIN -> it - MAX_SPEED - ZERO_MARGIN
                else -> 0.0
            }
        }.doOnDispose { dySubscribe.dispose() }
}

class DifferentialController(
    speedController: ISpeedController,
    turnController: ITurnController,
    stopped: Observable<Boolean>
) {
    val speed = speedController.speed
    val turn = turnController.turn
    val command: Observable<IControlCommand> = Observables.combineLatest(speed, turn, stopped) { s, t, st ->
        if (st) StopCommand
        else {
            val left = s - t
            val right = s + t
            val maxPower = max(left, right)
            val minPower = min(left, right)

            val offset = when {
                maxPower > 1 -> 1 - maxPower
                minPower < -1 -> -1 - minPower
                else -> 0.0
            }
            PowerCommand(left + offset, right + offset)
        }
    }
}
