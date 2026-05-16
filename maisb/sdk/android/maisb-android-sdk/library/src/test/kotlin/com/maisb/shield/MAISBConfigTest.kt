package com.maisb.shield

import org.junit.Test

class MAISBConfigTest {
    @Test
    fun testConfigValidation() {
        MAISBConfig(apiKey = "test_key", debug = true).validate()
    }

    @Test(expected = IllegalArgumentException::class)
    fun testEmptyAPIKeyFails() {
        MAISBConfig(apiKey = "").validate()
    }
}
