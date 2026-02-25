package com.maisb.harness

import android.app.Activity
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient

/**
 * WebViewActivity renders injected HTML for webview channel testing.
 * Started by the harness when a webview scenario is armed.
 */
class WebViewActivity : Activity() {

    companion object {
        const val EXTRA_HTML = "extra_html"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        webView.webViewClient = WebViewClient()
        webView.settings.javaScriptEnabled = false // JS disabled for safety
        setContentView(webView)

        val html = intent.getStringExtra(EXTRA_HTML)
            ?: "<html><body><p>No content loaded.</p></body></html>"
        webView.loadDataWithBaseURL("https://safe.example.com", html, "text/html", "UTF-8", null)
    }
}

