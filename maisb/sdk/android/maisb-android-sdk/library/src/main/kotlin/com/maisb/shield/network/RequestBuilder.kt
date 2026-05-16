package com.maisb.shield.network

import com.maisb.shield.models.ScanRequest
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody

object RequestBuilder {
    fun scanBody(json: Json, request: ScanRequest): RequestBody {
        return json.encodeToString(request)
            .toRequestBody("application/json".toMediaType())
    }
}
