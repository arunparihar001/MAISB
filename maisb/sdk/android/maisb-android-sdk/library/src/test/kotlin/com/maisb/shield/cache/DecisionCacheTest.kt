package com.maisb.shield.cache

import com.maisb.shield.models.Decision
import kotlin.test.Test
import kotlin.test.assertEquals

class DecisionCacheTest {
    @Test
    fun storesDecision() {
        val cache = DecisionCache()
        cache.put("payload", Decision.BLOCKED)
        assertEquals(Decision.BLOCKED, cache.get("payload"))
    }
}
