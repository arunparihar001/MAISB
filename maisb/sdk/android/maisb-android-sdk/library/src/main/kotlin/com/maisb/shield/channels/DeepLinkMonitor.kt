package com.maisb.shield.channels

import android.net.Uri

class DeepLinkMonitor {
    fun extractPayload(uri: Uri): String? {
        return uri.getQueryParameter("payload")
            ?: uri.getQueryParameter("text")
            ?: uri.getQueryParameter("url")
    }

    fun channel(): String = "deep_link"
}
