package com.maisb.shield.models

import kotlinx.serialization.Serializable

@Serializable
enum class Channel(val wireValue: String) {
    CLIPBOARD("clipboard"),
    NOTIFICATION("notification"),
    DEEP_LINK("deep_link"),
    WEBVIEW("webview"),
    QR_CODE("qr_code"),
    PDF_FILE("pdf_file"),
    SHARE_INTENT("share_intent"),
    INTERNAL_API("internal_api"),
    UNKNOWN("unknown");

    override fun toString(): String = wireValue
}
