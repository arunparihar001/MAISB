package com.maisb.shield

/**
 * Runtime configuration for the MAISB Android SDK.
 */
data class MAISBConfig(
    // Required
    val apiKey: String,
    val baseUrl: String = "https://api.maisb.app",

    // Enterprise / tenant configuration
    val tenantId: String = "default",
    val clientId: String = "android-agent",
    val integrationEnv: String = "production",

    // API Configuration
    val apiVersion: String = "v1",
    val timeout: Long = 30L,
    val retryAttempts: Int = 3,
    val retryDelayMs: Long = 1000,

    // Caching
    val cacheEnabled: Boolean = true,
    val cacheTtlMinutes: Int = 60,
    val maxCacheSize: Int = 100,

    // Monitoring
    val clipboardMonitoringEnabled: Boolean = true,
    val notificationMonitoringEnabled: Boolean = false,
    val deepLinkMonitoringEnabled: Boolean = false,

    // Telemetry
    val telemetryEnabled: Boolean = true,
    val batchTelemetryEnabled: Boolean = true,
    val batchSize: Int = 50,
    val batchIntervalMs: Long = 5000,

    // Security
    val encryptSensitiveData: Boolean = true,
    val validateSSLCertificates: Boolean = true,
    val pinCertificates: Boolean = false,
    val certificatePins: List<String> = emptyList(),

    // Debugging
    val debug: Boolean = BuildConfig.DEBUG,
    val logLevel: LogLevel = LogLevel.INFO
) {
    fun validate() {
        require(apiKey.isNotEmpty()) { "API key cannot be empty" }
        require(baseUrl.isNotEmpty()) { "Base URL cannot be empty" }
        require(tenantId.isNotEmpty()) { "Tenant ID cannot be empty" }
        require(timeout > 0) { "Timeout must be positive" }
        require(retryAttempts >= 0) { "Retry attempts must be >= 0" }
        require(maxCacheSize > 0) { "Max cache size must be positive" }
    }
}

enum class LogLevel {
    VERBOSE, DEBUG, INFO, WARNING, ERROR, NONE
}
