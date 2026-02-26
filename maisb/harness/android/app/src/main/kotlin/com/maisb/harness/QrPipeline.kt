package com.maisb.harness

import com.google.zxing.BarcodeFormat
import com.google.zxing.BinaryBitmap
import com.google.zxing.MultiFormatReader
import com.google.zxing.Result
import com.google.zxing.common.BitMatrix
import com.google.zxing.common.HybridBinarizer
import com.google.zxing.qrcode.QRCodeWriter
import com.google.zxing.RGBLuminanceSource

object QrPipeline {
    fun encodeDecode(text: String): String {
        val matrix: BitMatrix = QRCodeWriter().encode(text, BarcodeFormat.QR_CODE, 256, 256)
        val pixels = IntArray(256 * 256)
        for (y in 0 until 256) {
            for (x in 0 until 256) {
                pixels[y * 256 + x] = if (matrix[x, y]) 0xFF000000.toInt() else 0xFFFFFFFF.toInt()
            }
        }
        val source = RGBLuminanceSource(256, 256, pixels)
        val bitmap = BinaryBitmap(HybridBinarizer(source))
        val result: Result = MultiFormatReader().decode(bitmap)
        return result.text ?: ""
    }
}