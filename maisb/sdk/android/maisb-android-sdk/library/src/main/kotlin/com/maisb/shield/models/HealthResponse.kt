package com.maisb.shield.models

import kotlinx.serialization.Serializable

@Serializable
data class HealthResponse(
    val status: String = "unknown",
    val version: String? = null,
    val phase2: Boolean? = null,
    val phase3: Boolean? = null,
    val phase4: Boolean? = null
)
