package com.maisb.harness

import kotlinx.serialization.Serializable

/**
 * Holds the current injected state for each channel.
 * Thread-safety: use @Volatile or synchronize externally.
 */
@Serializable
data class ChannelState(
    @Volatile var lastClipboardText: String = "",
    @Volatile var lastDeeplinkUrl: String = "",
    @Volatile var lastShareText: String = "",
    @Volatile var lastQrText: String = "",
    @Volatile var lastWebViewText: String = "",
    @Volatile var lastNotificationText: String = "",
    @Volatile var lastWebViewHtml: String = "",
)
