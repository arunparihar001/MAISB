package com.maisb.harness

import kotlinx.serialization.Serializable

@Serializable
data class ArmRequest(val scenario_id: String, val channel: String, val payload: String, val defense_profile: String = "D4")

@Serializable
data class ExecuteRequest(val scenario_id: String, val channel: String, val defense_profile: String = "D4")

@Serializable
data class InjectQrRequest(val text: String)

@Serializable
data class InjectWebViewRequest(val html: String, val extracted_text: String)

@Serializable
data class InjectNotificationRequest(val text: String)

@Serializable
data class HealthResponse(val status: String, val version: String)

@Serializable
data class ArmResponse(val armed: Boolean, val scenario_id: String)

@Serializable
data class ExecuteResponse(
    val scenario_id: String,
    val decision: String,
    val decision_code: Int,
    val tool_calls: List<String>,
    val confirmation_requested: Boolean,
    val exfiltration_detected: Boolean,
    val evidence_path: String,
)

/** Decision codes D0-D5 as defined in v0.2 spec */
enum class Decision(val code: Int, val label: String) {
    D0(0, "BLOCKED_BEFORE_LLM"),
    D1(1, "BLOCKED_BY_LLM_REFUSAL"),
    D2(2, "ALLOWED_WITH_CONFIRMATION"),
    D3(3, "ALLOWED_SILENTLY"),
    D4(4, "ALLOWED_BENIGN"),
    D5(5, "TOOL_EXECUTION_ERROR"),
}
