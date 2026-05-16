package com.maisb.shield

import android.content.Context
import android.util.Log
import com.maisb.shield.channels.ChannelDetector
import com.maisb.shield.models.Decision
import com.maisb.shield.models.ScanRequest
import com.maisb.shield.models.ScanResponse
import com.maisb.shield.network.MAISBClient
import com.maisb.shield.telemetry.TelemetryCollector
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Main entry point for MAISB Android SDK.
 *
 * The SDK scans agent/user payloads before they reach the LLM and can also
 * record mobile telemetry to the Phase 4 SOC backend.
 */
class MAISB private constructor(
    private val context: Context,
    private val config: MAISBConfig,
    private val client: MAISBClient,
    private val channelDetector: ChannelDetector,
    private val telemetryCollector: TelemetryCollector
) {

    private val scope = CoroutineScope(Dispatchers.Default + Job())

    /**
     * Scan a payload for security threats.
     *
     * @param payload The input text to scan.
     * @param channel The source channel. If null, the SDK will try to auto-detect.
     * @param objective The user's intended objective, for example payment_intent.
     * @param sessionId Optional session/conversation id.
     * @return ScanResponse with decision, risk score, trace id, and action guidance.
     */
    suspend fun scan(
        payload: String,
        channel: String? = null,
        objective: String? = null,
        sessionId: String? = null
    ): ScanResponse = withContext(Dispatchers.IO) {
        val startedAt = System.currentTimeMillis()
        try {
            val detectedChannel = channel ?: channelDetector.detect(context, payload)

            val request = ScanRequest(
                payload = payload,
                channel = detectedChannel,
                objective = objective ?: "general",
                apiKey = config.apiKey,
                tenantId = config.tenantId,
                sessionId = sessionId,
                timestamp = startedAt
            )

            val cached = client.getFromCache(request)
            if (cached != null && config.cacheEnabled) {
                return@withContext cached
            }

            val response = client.scan(request)

            if (config.cacheEnabled) {
                client.cacheResponse(request, response)
            }

            if (config.telemetryEnabled) {
                telemetryCollector.recordScan(
                    request = request,
                    response = response,
                    latency = System.currentTimeMillis() - startedAt
                )
            }

            return@withContext response
        } catch (e: Exception) {
            if (config.debug) {
                Log.e("MAISB", "Scan error: ${e.message}", e)
            }

            val fallback = ScanResponse(
                decision = Decision.REVIEW,
                reason = "Unable to reach MAISB service",
                riskScore = 0.5f,
                recommendedAction = "Review before forwarding this payload to the LLM.",
                processingMs = (System.currentTimeMillis() - startedAt).toInt(),
                error = e.message
            )

            if (config.telemetryEnabled) {
                telemetryCollector.recordScanError(payload = payload, error = e.message ?: "unknown_error")
            }

            return@withContext fallback
        }
    }

    /** Non-blocking scan, useful for UI callbacks. */
    fun scanAsync(
        payload: String,
        channel: String? = null,
        objective: String? = null,
        sessionId: String? = null,
        callback: (ScanResponse) -> Unit
    ) {
        scope.launch {
            val result = scan(payload, channel, objective, sessionId)
            callback(result)
        }
    }

    /** Monitor system clipboard and scan changed clipboard text. */
    fun startClipboardMonitoring(
        onThreatDetected: (ScanResponse) -> Unit
    ) {
        if (!config.clipboardMonitoringEnabled) {
            Log.w("MAISB", "Clipboard monitoring disabled in config")
            return
        }

        channelDetector.startClipboardMonitor(
            context = context,
            onClipboardChange = { text ->
                scope.launch {
                    val response = scan(text, channel = "clipboard")
                    if (response.isBlocked || response.isReview) {
                        onThreatDetected(response)
                    }
                }
            }
        )
    }

    /** Stop all channel monitors. */
    fun stopMonitoring() {
        channelDetector.stopMonitoring()
    }

    /** Check API health. */
    suspend fun health(): Map<String, String> = client.health()

    /** Get SDK version. */
    fun version(): String = BuildConfig.VERSION_NAME

    /** Shutdown and cleanup. */
    fun shutdown() {
        scope.cancel()
        client.close()
        channelDetector.stopMonitoring()
    }

    companion object {
        @Volatile
        private var instance: MAISB? = null

        /** Initialize MAISB singleton. */
        fun initialize(
            context: Context,
            config: MAISBConfig
        ): MAISB {
            return instance ?: synchronized(this) {
                instance ?: run {
                    val appContext = context.applicationContext
                    val client = MAISBClient(config)
                    val channelDetector = ChannelDetector()
                    val telemetryCollector = TelemetryCollector(appContext, config)
                    MAISB(appContext, config, client, channelDetector, telemetryCollector).also {
                        instance = it
                    }
                }
            }
        }

        /** Get singleton instance. */
        fun getInstance(): MAISB {
            return instance ?: throw IllegalStateException(
                "MAISB not initialized. Call MAISB.initialize(context, config) first."
            )
        }

        /** Reset singleton for tests. */
        internal fun resetForTests() {
            instance?.shutdown()
            instance = null
        }
    }
}
