package com.maisb.shield.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Mobile SDK telemetry reported to Phase 4 SOC endpoint. */
@Serializable
data class TelemetryData(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("sdk_version") val sdkVersion: String,
    @SerialName("client_type") val clientType: String = "android",
    @SerialName("client_id") val clientId: String = "android-agent",
    @SerialName("integration_env") val integrationEnv: String = "production",
    @SerialName("device_id") val deviceId: String? = null,
    @SerialName("session_id") val sessionId: String? = null,
    val channel: String? = null,
    val objective: String? = null,
    val decision: String? = null,
    @SerialName("risk_score") val riskScore: Float? = null,
    @SerialName("trace_id") val traceId: String? = null,
    @SerialName("event_id") val eventId: String? = null,
    @SerialName("latency_ms") val latencyMs: Long? = null,
    val metadata: Map<String, String> = emptyMap(),
    val timestamp: Long = System.currentTimeMillis()
)
