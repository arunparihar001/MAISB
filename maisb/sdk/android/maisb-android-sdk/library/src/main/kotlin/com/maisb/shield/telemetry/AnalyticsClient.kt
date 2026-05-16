package com.maisb.shield.telemetry

import com.maisb.shield.MAISBConfig
import com.maisb.shield.models.TelemetryData
import com.maisb.shield.network.MAISBClient

class AnalyticsClient(config: MAISBConfig) {
    private val client = MAISBClient(config)

    suspend fun sendTelemetry(telemetry: TelemetryData): Boolean {
        return client.sendTelemetry(telemetry)
    }

    fun close() = client.close()
}
