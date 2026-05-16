package com.maisb.shield.network

import android.util.Log
import com.maisb.shield.MAISBConfig
import com.maisb.shield.LogLevel
import okhttp3.Interceptor
import okhttp3.Response

class MAISBInterceptor(
    private val config: MAISBConfig
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val request = original.newBuilder()
            .header("X-Tenant-ID", config.tenantId)
            .header("X-MAISB-Client", config.clientId)
            .build()
        return chain.proceed(request)
    }
}

class LoggingInterceptor(
    private val config: MAISBConfig
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        if (config.debug && config.logLevel <= LogLevel.DEBUG) {
            Log.d("MAISBHttp", "${request.method} ${request.url}")
        }
        val start = System.currentTimeMillis()
        val response = chain.proceed(request)
        if (config.debug && config.logLevel <= LogLevel.INFO) {
            Log.i("MAISBHttp", "${response.code} ${request.url.encodedPath} ${System.currentTimeMillis() - start}ms")
        }
        return response
    }
}
