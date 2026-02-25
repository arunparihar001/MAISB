package com.maisb.harness

import kotlinx.serialization.Serializable

@Serializable
data class ToolCallJson(
    val name: String,
    val args: Map<String, String> = emptyMap()
)

@Serializable
data class LLMResponseJson(
    val refusal: Boolean = false,
    val tool_calls: List<ToolCallJson> = emptyList(),
    val final: String = ""
)
