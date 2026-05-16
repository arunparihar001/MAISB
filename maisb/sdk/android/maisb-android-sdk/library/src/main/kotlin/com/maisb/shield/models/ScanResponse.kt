package com.maisb.shield.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Response from MAISB API. */
@Serializable
data class ScanResponse(
    val decision: Decision = Decision.UNKNOWN,
    @SerialName("risk_score") val riskScore: Float = 0.0f,
    val confidence: Float = 1.0f,
    @SerialName("taxonomy_class") val taxonomyClass: String? = null,
    @SerialName("recommended_action") val recommendedAction: String? = null,
    val reasoning: List<String> = emptyList(),
    @SerialName("triggered_rules") val triggeredRules: List<String> = emptyList(),
    @SerialName("processing_ms") val processingMs: Int = 0,
    @SerialName("latency_ms") val latencyMs: Long = processingMs.toLong(),
    @SerialName("trace_id") val traceId: String? = null,
    @SerialName("event_id") val eventId: String? = null,
    val reason: String? = null,
    val error: String? = null
) {
    val isBlocked: Boolean get() = decision == Decision.BLOCKED
    val isReview: Boolean get() = decision == Decision.REVIEW
    val isAllowed: Boolean get() = decision == Decision.ALLOWED
}
