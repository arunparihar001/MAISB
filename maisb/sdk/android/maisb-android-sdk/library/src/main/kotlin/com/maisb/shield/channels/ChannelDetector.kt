package com.maisb.shield.channels

import android.content.ClipboardManager
import android.content.Context

class ChannelDetector {
    private var clipboardMonitor: ClipboardMonitor? = null
    private val monitors = mutableListOf<BaseMonitor>()

    /** Auto-detect channel from context. */
    fun detect(context: Context, payload: String): String {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        val clipText = clipboard?.primaryClip?.takeIf { it.itemCount > 0 }
            ?.getItemAt(0)?.text?.toString()
        if (!payload.isBlank() && clipText == payload) {
            return "clipboard"
        }
        return "unknown"
    }

    fun startClipboardMonitor(
        context: Context,
        onClipboardChange: (String) -> Unit
    ) {
        if (clipboardMonitor != null) return
        clipboardMonitor = ClipboardMonitor(context, onClipboardChange)
        clipboardMonitor!!.startMonitoring()
        monitors.add(clipboardMonitor!!)
    }

    fun stopMonitoring() {
        monitors.forEach { it.stopMonitoring() }
        monitors.clear()
        clipboardMonitor = null
    }
}

abstract class BaseMonitor {
    abstract fun startMonitoring()
    abstract fun stopMonitoring()
}
