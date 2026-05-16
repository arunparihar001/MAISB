package com.maisb.shield.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Input request for scanning. */
@Serializable
data class ScanRequest(
    val payload: String,
    val channel: String,
    val objective: String? = "general",
    @SerialName("api_key") val apiKey: String? = null,
    @SerialName("tenant_id") val tenantId: String? = null,
    @SerialName("session_id") val sessionId: String? = null,
    val timestamp: Long = System.currentTimeMillis()
)
