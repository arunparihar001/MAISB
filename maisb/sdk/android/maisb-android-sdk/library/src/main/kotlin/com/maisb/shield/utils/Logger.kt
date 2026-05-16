package com.maisb.shield.utils

import android.util.Log
import com.maisb.shield.LogLevel

class Logger(
    private val tag: String,
    private val level: LogLevel = LogLevel.INFO
) {
    fun d(message: String) { if (level <= LogLevel.DEBUG) Log.d(tag, message) }
    fun i(message: String) { if (level <= LogLevel.INFO) Log.i(tag, message) }
    fun w(message: String) { if (level <= LogLevel.WARNING) Log.w(tag, message) }
    fun e(message: String, throwable: Throwable? = null) { if (level <= LogLevel.ERROR) Log.e(tag, message, throwable) }
}
