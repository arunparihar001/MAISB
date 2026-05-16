package com.maisb.shield.utils

import com.maisb.shield.models.Decision
import com.maisb.shield.models.ScanResponse

fun ScanResponse.shouldBlockAgentAction(): Boolean = decision == Decision.BLOCKED

fun ScanResponse.summary(): String {
    return "decision=$decision risk=$riskScore trace=${traceId ?: "none"}"
}
