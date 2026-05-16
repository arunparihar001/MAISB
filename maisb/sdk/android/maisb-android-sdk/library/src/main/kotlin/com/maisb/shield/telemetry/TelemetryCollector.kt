package com.maisb.shield.telemetry

import android.content.Context
import android.provider.Settings
import android.util.Log
import com.maisb.shield.BuildConfig
import com.maisb.shield.MAISBConfig
import com.maisb.shield.models.ScanRequest
import com.maisb.shield.models.ScanResponse
import com.maisb.shield.models.TelemetryData
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

class TelemetryCollector(
    private val context: Context,
    private val config: MAISBConfig
) {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val analyticsClient = AnalyticsClient(config)
    private val scansPerformed = AtomicInteger(0)
    private val blockedCount = AtomicInteger(0)
    private val totalLatency = AtomicLong(0L)

    fun recordScan(
        request: ScanRequest,
        response: ScanResponse,
        latency: Long
    ) {
        scansPerformed.incrementAndGet()
        totalLatency.addAndGet(latency)
        if (response.isBlocked) blockedCount.incrementAndGet()

        val telemetry = TelemetryData(
            tenantId = config.tenantId,
            sdkVersion = BuildConfig.VERSION_NAME,
            clientType = "android",
            clientId = config.clientId,
            integrationEnv = config.integrationEnv,
            deviceId = getDeviceId(),
            sessionId = request.sessionId,
            channel = request.channel,
            objective = request.objective,
            decision = response.decision.name,
            riskScore = response.riskScore,
            traceId = response.traceId,
            eventId = response.eventId,
            latencyMs = latency,
            metadata = mapOf(
                "taxonomy_class" to response.taxonomyClass.orEmpty(),
                "processing_ms" to response.processingMs.toString(),
                "scans_performed" to scansPerformed.get().toString(),
                "blocked_count" to blockedCount.get().toString(),
                "average_latency_ms" to averageLatency().toString()
            )
        )

        send(telemetry)
    }

    fun recordScanError(payload: String, error: String) {
        val telemetry = TelemetryData(
            tenantId = config.tenantId,
            sdkVersion = BuildConfig.VERSION_NAME,
            clientType = "android",
            clientId = config.clientId,
            integrationEnv = config.integrationEnv,
            deviceId = getDeviceId(),
            channel = "unknown",
            decision = "ERROR",
            riskScore = null,
            metadata = mapOf(
                "error" to error,
                "payload_length" to payload.length.toString()
            )
        )
        send(telemetry)
    }

    private fun send(telemetry: TelemetryData) {
        if (!config.telemetryEnabled) return
        scope.launch {
            val ok = analyticsClient.sendTelemetry(telemetry)
            if (config.debug && !ok) {
                Log.w("MAISBTelemetry", "Telemetry delivery failed")
            }
        }
    }

    private fun averageLatency(): Long {
        val count = scansPerformed.get().coerceAtLeast(1)
        return totalLatency.get() / count
    }

    private fun getDeviceId(): String? {
        return try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        } catch (_: Exception) {
            null
        }
    }
}
