package cn.huww98.picontroller

import android.content.Context
import android.content.Context.WIFI_SERVICE
import android.net.wifi.WifiManager
import android.util.Log
import io.reactivex.Observable
import io.reactivex.disposables.CompositeDisposable
import io.reactivex.schedulers.Schedulers
import java.net.*
import java.util.concurrent.TimeUnit


data class RobotConnectionInfo(
    val address: InetAddress,
    val localAddress: InetAddress
)

class RobotDiscovery(private val ctx: Context) {
    companion object {
        val groupV4: InetAddress = InetAddress.getByName("239.255.255.250")
        val groupV6: InetAddress = InetAddress.getByName("ff02::f")

        const val type = "urn:pirobot-huww98-cn:device:PiRobot:1"
        const val port = 1900
        const val query = "M-SEARCH * HTTP/1.1\r\n" +
                "HOST: %s:$port\r\n" +
                "MAN: \"ssdp:discover\"\r\n" +
                "MX: 1\r\n" +
                "ST: $type\r\n" +
                "\r\n"

        const val tag = "Discover"
    }

    private fun getWlanAddresses(): Sequence<InetAddress> {
        return getWlanInterfaces()
            .flatMap { it.inetAddresses.asSequence() }
    }

    private fun getWlanInterfaces(): Sequence<NetworkInterface> {
        return NetworkInterface.getNetworkInterfaces()
            .asSequence()
            .filter { it.name.contains("wlan") }
    }

    fun discover(): Observable<RobotConnectionInfo> {
        val wifi = ctx.applicationContext.getSystemService(WIFI_SERVICE) as WifiManager
        val lock = wifi.createMulticastLock("Pi Controller - Discover robot")
        lock.acquire()
        val connectionInfo = ArrayList<Observable<RobotConnectionInfo>>()
        getWlanInterfaces().forEach { inf ->
            val notify = Observable.create<RobotConnectionInfo> { emitter ->
                val socket = MulticastSocket(port)
                socket.joinGroup(InetSocketAddress(groupV4, port), inf)
                var finished = false
                emitter.setCancellable {
                    finished = true
                    socket.close()
                }
                Log.d(tag, "Listening notify on ${inf.displayName}")
                while (!finished) {
                    val buffer = ByteArray(2048)
                    val packet = DatagramPacket(buffer, buffer.size)
                    try {
                        socket.receive(packet)
                    } catch (_: SocketException) { // In case of cancelled by socket.close()
                        break
                    }
                    val lines = packet.data.toString(Charsets.UTF_8).lines()
                    if (lines[0] != "NOTIFY * HTTP/1.1" ||
                            !lines.contains("NTS: ssdp:alive")) {
                        continue
                    }
                    val nt = lines.filter { it.startsWith("NT:") }.map { it.substring(3).trim() }.firstOrNull()
                        ?: continue
                    if (nt == type) {
                        val remoteAddress = packet.address
                        Log.d(tag, "Got $remoteAddress from NOTIFY")
                        val localAddress = inf.inetAddresses.asSequence().first { it::class == remoteAddress::class }
                        emitter.onNext(RobotConnectionInfo(remoteAddress, localAddress))
                    }
                }
                Log.d(tag, "Finished listen NOTIFY on ${inf.displayName}")
                emitter.onComplete()
            }
            connectionInfo.add(notify.subscribeOn(Schedulers.io()))
        }

        val disposables = CompositeDisposable()
        getWlanAddresses().forEach { addr ->
            val socket = DatagramSocket(0, addr)
            val response = Observable.create<RobotConnectionInfo> { emitter ->
                val time = System.currentTimeMillis()
                var curTime = System.currentTimeMillis()
                socket.soTimeout = 2000

                Log.d(tag, "Listening response on $addr")
                // Let's consider all the responses we can get in 1 second
                while (curTime - time < 2000) {
                    val p = DatagramPacket(ByteArray(12), 12)
                    try {
                        socket.receive(p)
                        val s = p.data.toString(Charsets.UTF_8)
                        if (s == "HTTP/1.1 200") {
                            val remoteAddress = p.address
                            Log.d(tag, "Got $remoteAddress from response")
                            emitter.onNext(RobotConnectionInfo(remoteAddress, addr))
                        }
                        curTime = System.currentTimeMillis()
                    } catch (_: SocketTimeoutException) {
                        break
                    }
                }
                Log.d(tag, "Finished listen response on $addr")
                emitter.onComplete()
            }
            connectionInfo.add(response.subscribeOn(Schedulers.io()))

            val (group, groupTxt) = when (addr) {
                is Inet4Address -> Pair(groupV4, groupV4.hostAddress)
                is Inet6Address -> Pair(groupV6, "[${groupV6.hostAddress}]")
                else -> throw NotImplementedError()
            }

            val queryBuffer = query.format(groupTxt).toByteArray()
            val datagram = DatagramPacket(queryBuffer, queryBuffer.size, group, port)
            val sendingDisposable = Observable.interval(200, TimeUnit.MILLISECONDS)
                .take(3)
                .subscribe {
                    Log.d(tag, "Sending SSDP:Discover on $addr.")
                    socket.send(datagram)
                }
            disposables.add(sendingDisposable)
        }
        return Observable.merge(connectionInfo)
            .distinct()
            .doOnDispose {
                disposables.dispose()
                lock.release()
            }
    }
}
