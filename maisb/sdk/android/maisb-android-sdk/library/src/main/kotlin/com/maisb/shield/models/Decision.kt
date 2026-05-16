package com.maisb.shield.models

import kotlinx.serialization.Serializable

@Serializable
enum class Decision {
    BLOCKED,
    REVIEW,
    ALLOWED,
    UNKNOWN
}
