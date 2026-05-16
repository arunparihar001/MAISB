package com.maisb.sample

import android.app.Application
import com.maisb.shield.MAISB
import com.maisb.shield.MAISBConfig

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        val config = MAISBConfig(
            apiKey = BuildConfig.MAISB_API_KEY,
            tenantId = "default",
            debug = BuildConfig.DEBUG,
            telemetryEnabled = true
        )

        MAISB.initialize(this, config)
    }
}
