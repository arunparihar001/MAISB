package com.maisb.harness

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val tv = TextView(this)
        tv.text = "MAISB Harness v0.3 - Server running on port 8765"
        setContentView(tv)

        Thread {
            HarnessServer(filesDir).start()
        }.start()
    }
}
