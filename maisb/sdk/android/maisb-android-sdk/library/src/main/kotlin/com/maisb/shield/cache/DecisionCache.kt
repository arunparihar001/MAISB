package com.maisb.shield.cache

import com.maisb.shield.models.Decision
import java.util.concurrent.ConcurrentHashMap

class DecisionCache {
    private val decisions = ConcurrentHashMap<String, Decision>()

    fun put(key: String, decision: Decision) {
        decisions[key] = decision
    }

    fun get(key: String): Decision? = decisions[key]

    fun clear() = decisions.clear()
}
