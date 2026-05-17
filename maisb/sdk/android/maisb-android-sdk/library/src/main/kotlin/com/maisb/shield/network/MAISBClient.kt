package com.maisb.shield.network

import com.maisb.shield.BuildConfig
import com.maisb.shield.MAISBConfig
import com.maisb.shield.cache.ResponseCache
import com.maisb.shield.models.HealthResponse
import com.maisb.shield.models.ScanRequest
import com.maisb.shield.models.ScanResponse
import com.maisb.shield.models.TelemetryData
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.Callback
import okhttp3.CertificatePinner
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class MAISBClient(
    private val config: MAISBConfig
) {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    private val cache = ResponseCache(config)
    private val httpClient: OkHttpClient

    init {
        config.validate()
        httpClient = buildHttpClient()
    }

    private fun buildHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(config.timeout, TimeUnit.SECONDS)
            .readTimeout(config.timeout, TimeUnit.SECONDS)
            .writeTimeout(config.timeout, TimeUnit.SECONDS)
            .addInterceptor(MAISBInterceptor(config))
            .addNetworkInterceptor(LoggingInterceptor(config))
            .retryOnConnectionFailure(config.retryAttempts > 0)
            .apply {
                if (config.pinCertificates) {
                    certificatePinner(buildCertificatePinner())
                }
            }
            .build()
    }

    suspend fun scan(request: ScanRequest): ScanResponse {
        var lastError: Throwable? = null
        repeat(config.retryAttempts + 1) { attempt ->
            try {
                return doScan(request)
            } catch (e: Throwable) {
                lastError = e
                if (attempt < config.retryAttempts) {
                    delay(config.retryDelayMs)
                }
            }
        }
        throw lastError ?: IOException("Unknown MAISB scan error")
    }

    private suspend fun doScan(request: ScanRequest): ScanResponse {
        val url = buildUrl("/scan")
        val body = RequestBuilder.scanBody(json, request)

        val httpRequest = Request.Builder()
            .url(url)
            .post(body)
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer ${config.apiKey}")
            .header("X-Tenant-ID", config.tenantId)
            .header("X-Client-Version", BuildConfig.VERSION_NAME)
            .header("X-Client-Platform", "android")
            .build()

        return executeJson(httpRequest)
    }

    suspend fun sendTelemetry(telemetry: TelemetryData): Boolean {
        return try {
            val url = buildUrl("/sdk/mobile/telemetry")
            val body = json.encodeToString(telemetry)
                .toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(body)
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer ${config.apiKey}")
                .header("X-Tenant-ID", config.tenantId)
                .header("X-Client-Version", BuildConfig.VERSION_NAME)
                .header("X-Client-Platform", "android")
                .build()

            executeRaw(request).use { response -> response.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    suspend fun health(): Map<String, String> {
        val request = Request.Builder()
            .url(trimBaseUrl(config.baseUrl) + "/health")
            .get()
            .build()
        val response: HealthResponse = executeJson(request)
        return buildMap {
            put("status", response.status)
            response.version?.let { put("version", it) }
            response.phase2?.let { put("phase2", it.toString()) }
            response.phase3?.let { put("phase3", it.toString()) }
            response.phase4?.let { put("phase4", it.toString()) }
        }
    }

    fun getFromCache(request: ScanRequest): ScanResponse? {
        if (!config.cacheEnabled) return null
        return cache.get(request)
    }

    fun cacheResponse(request: ScanRequest, response: ScanResponse) {
        if (config.cacheEnabled) cache.put(request, response)
    }

    fun clearCache() = cache.clear()

    private fun buildUrl(endpoint: String): String {
        val cleanEndpoint = endpoint.trimStart('/')
        return "${trimBaseUrl(config.baseUrl)}/${config.apiVersion}/$cleanEndpoint"
    }

    private fun trimBaseUrl(url: String): String = url.trimEnd('/')

    private fun buildCertificatePinner(): CertificatePinner {
        val builder = CertificatePinner.Builder()
        val host = trimBaseUrl(config.baseUrl).toHttpUrlOrNull()?.host
        config.certificatePins.forEach { pin ->
            if (host != null) {
                builder.add(host, pin)
            }
        }
        return builder.build()
    }

    private suspend inline fun <reified T> executeJson(request: Request): T {
        val response = executeRaw(request)
        response.use {
            val body = response.body?.string() ?: throw IOException("Empty response body")
            if (!response.isSuccessful) {
                throw IOException("HTTP ${response.code}: $body")
            }
            return json.decodeFromString(body)
        }
    }

    private suspend fun executeRaw(request: Request): Response = suspendCancellableCoroutine { continuation ->
        val call = httpClient.newCall(request)
        continuation.invokeOnCancellation { call.cancel() }
        call.enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                if (!continuation.isCancelled) continuation.resumeWithException(e)
            }

            override fun onResponse(call: Call, response: Response) {
                if (!continuation.isCancelled) continuation.resume(response)
            }
        })
    }

    fun close() {
        httpClient.dispatcher.executorService.shutdown()
        httpClient.connectionPool.evictAll()
    }
}
