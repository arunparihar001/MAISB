package com.maisb.shield.security

import android.content.Context

class APIKeyManager(context: Context) {
    private val storage = SecureStorage(context)

    fun saveApiKey(apiKey: String) {
        storage.putString(KEY_API_KEY, apiKey)
    }

    fun getApiKey(): String? = storage.getString(KEY_API_KEY)

    fun clearApiKey() {
        storage.remove(KEY_API_KEY)
    }

    companion object {
        private const val KEY_API_KEY = "maisb_api_key"
    }
}
