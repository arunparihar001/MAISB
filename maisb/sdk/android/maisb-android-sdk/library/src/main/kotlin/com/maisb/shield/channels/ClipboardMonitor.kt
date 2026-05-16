package com.maisb.shield.channels

import android.content.ClipboardManager
import android.content.Context
import android.os.Handler
import android.os.Looper

class ClipboardMonitor(
    private val context: Context,
    private val onPrimaryClipChanged: (String) -> Unit
) : BaseMonitor() {
    private val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    private val handler = Handler(Looper.getMainLooper())
    private var lastClipText = ""
    private var monitoring = false

    override fun startMonitoring() {
        if (monitoring) return
        monitoring = true
        handler.post(object : Runnable {
            override fun run() {
                if (!monitoring) return
                val clipData = clipboard.primaryClip
                if (clipData != null && clipData.itemCount > 0) {
                    val text = clipData.getItemAt(0).text?.toString().orEmpty()
                    if (text.isNotEmpty() && text != lastClipText) {
                        lastClipText = text
                        onPrimaryClipChanged(text)
                    }
                }
                handler.postDelayed(this, 1000)
            }
        })
    }

    override fun stopMonitoring() {
        monitoring = false
        handler.removeCallbacksAndMessages(null)
    }
}
