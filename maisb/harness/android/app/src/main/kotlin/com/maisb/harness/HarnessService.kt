package com.maisb.harness

import android.app.Service
import android.content.Intent
import android.os.IBinder

class HarnessService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Thread {
            HarnessServer(filesDir).start()
        }.start()
        return START_STICKY
    }
}
