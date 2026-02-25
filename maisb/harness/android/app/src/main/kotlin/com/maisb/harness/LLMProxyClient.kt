package com.maisb.harness

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

@Serializable
data class ProxyGenerateRequest(
    val provider: String,
    val model: String,
    val system: String = "",
    val user: String,
    val temperature: Double = 0.0,
    val max_tokens: Int = 600
)

@Serializable
data class ProxyGenerateResponse(
    val provider: String,
    val model: String,
    val latency_ms: Int,
    val text: String
)

class LLMProxyClient(
    private val baseUrl: String = "http://10.0.2.2:9000"
) {
    private val json = Json { ignoreUnknownKeys = true; prettyPrint = false }

    fun generate(provider: String, model: String, system: String, user: String): ProxyGenerateResponse {
        val url = URL("$baseUrl/generate")
        val conn = (url.openConnection() as HttpURLConnection)
        conn.requestMethod = "POST"
        conn.setRequestProperty("Content-Type", "application/json")
        conn.doOutput = true
        conn.connectTimeout = 30_000
        conn.readTimeout = 60_000

        val payload = ProxyGenerateRequest(
            provider = provider,
            model = model,
            system = system,
            user = user
        )

        OutputStreamWriter(conn.outputStream).use { it.write(json.encodeToString(ProxyGenerateRequest.serializer(), payload)) }

        val code = conn.responseCode
        val body = (if (code in 200..299) conn.inputStream else conn.errorStream)
            .bufferedReader().use { it.readText() }

        if (code !in 200..299) {
            throw RuntimeException("LLM proxy error $code: $body")
        }
        return json.decodeFromString(ProxyGenerateResponse.serializer(), body)
    }
}
