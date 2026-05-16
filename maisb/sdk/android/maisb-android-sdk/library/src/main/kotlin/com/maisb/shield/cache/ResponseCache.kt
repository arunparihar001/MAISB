package com.maisb.shield.cache

import android.util.LruCache
import com.maisb.shield.MAISBConfig
import com.maisb.shield.models.ScanRequest
import com.maisb.shield.models.ScanResponse
import java.security.MessageDigest

class ResponseCache(
    private val config: MAISBConfig
) {
    private data class Entry(
        val response: ScanResponse,
        val expiresAt: Long
    )

    private val cache = LruCache<String, Entry>(config.maxCacheSize)

    fun get(request: ScanRequest): ScanResponse? {
        val entry = cache.get(cacheKey(request)) ?: return null
        if (System.currentTimeMillis() > entry.expiresAt) {
            cache.remove(cacheKey(request))
            return null
        }
        return entry.response
    }

    fun put(request: ScanRequest, response: ScanResponse) {
        val ttlMs = config.cacheTtlMinutes * 60_000L
        cache.put(cacheKey(request), Entry(response, System.currentTimeMillis() + ttlMs))
    }

    fun clear() = cache.evictAll()

    private fun cacheKey(request: ScanRequest): String {
        val raw = listOf(
            request.payload,
            request.channel,
            request.objective.orEmpty(),
            request.tenantId.orEmpty()
        ).joinToString("|")
        return sha256(raw)
    }

    private fun sha256(value: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(value.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }
}
