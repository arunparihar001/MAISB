# docs/PHASE4_TEST_COMMANDS.ps1
$BaseUrl = "http://127.0.0.1:8001"
$TenantId = "default"
$AdminKey = "change_me_in_production"
$Headers = @{
  "Authorization" = "Bearer $AdminKey"
  "X-MAISB-Role" = "admin"
}

Write-Host "`n[1] Phase 4 health" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/phase4/health?tenant_id=$TenantId" -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "`n[2] Auth check" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/security/auth/check?tenant_id=$TenantId&required_permission=case:read" -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "`n[3] Create SOC case" -ForegroundColor Cyan
$caseBody = @{
  tenant_id = $TenantId
  trace_id = "trace_phase4_demo"
  title = "High-risk cross-channel prompt injection investigation"
  severity = "high"
  priority = 2
  owner = "analyst1"
  risk_score = 0.92
  source_channel = "clipboard"
  detection_layer = "webview"
  tags = @("phase4", "soc", "prompt-injection")
  evidence = @{
    reason = "Malicious payload crossed channel boundary"
    decision = "BLOCKED"
  }
} | ConvertTo-Json -Depth 10

$case = Invoke-RestMethod "$BaseUrl/v1/soc/cases" -Method POST -ContentType "application/json" -Headers $Headers -Body $caseBody
$case | ConvertTo-Json -Depth 10
$CaseId = $case.case_id

Write-Host "`n[4] Add comment" -ForegroundColor Cyan
$commentBody = @{
  author = "analyst1"
  comment = "Initial triage complete. Payload should remain blocked and trace should be reviewed."
  visibility = "internal"
} | ConvertTo-Json
Invoke-RestMethod "$BaseUrl/v1/soc/cases/$CaseId/comments?tenant_id=$TenantId" -Method POST -ContentType "application/json" -Headers $Headers -Body $commentBody | ConvertTo-Json -Depth 10

Write-Host "`n[5] Assign case" -ForegroundColor Cyan
$assignBody = @{
  owner = "soc-lead"
  actor = "analyst1"
} | ConvertTo-Json
Invoke-RestMethod "$BaseUrl/v1/soc/cases/$CaseId/assign?tenant_id=$TenantId" -Method POST -ContentType "application/json" -Headers $Headers -Body $assignBody | ConvertTo-Json -Depth 10

Write-Host "`n[6] Update status" -ForegroundColor Cyan
$statusBody = @{
  status = "investigating"
  reason = "Escalated for SOC review"
  actor = "soc-lead"
} | ConvertTo-Json
Invoke-RestMethod "$BaseUrl/v1/soc/cases/$CaseId/status?tenant_id=$TenantId" -Method POST -ContentType "application/json" -Headers $Headers -Body $statusBody | ConvertTo-Json -Depth 10

Write-Host "`n[7] Case timeline" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/soc/cases/$CaseId/timeline?tenant_id=$TenantId" -Headers $Headers | ConvertTo-Json -Depth 20

Write-Host "`n[8] Risk queue" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/soc/risk-queue?tenant_id=$TenantId&min_risk=0.5" -Headers $Headers | ConvertTo-Json -Depth 20

Write-Host "`n[9] Search cases" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/soc/search?tenant_id=$TenantId&q=prompt" -Headers $Headers | ConvertTo-Json -Depth 20

Write-Host "`n[10] Mobile SDK telemetry" -ForegroundColor Cyan
$telemetryBody = @{
  tenant_id = $TenantId
  trace_id = "trace_phase4_demo"
  session_id = "sess_demo_001"
  device_id = "android-test-device"
  sdk_version = "0.4.0"
  app_package = "com.maisb.demo"
  platform = "android"
  channel = "clipboard"
  decision = "BLOCKED"
  risk_score = 0.92
  latency_ms = 42
  details = @{
    network = "wifi"
    source = "phase4_test_script"
  }
} | ConvertTo-Json -Depth 10
Invoke-RestMethod "$BaseUrl/v1/sdk/mobile/telemetry" -Method POST -ContentType "application/json" -Headers $Headers -Body $telemetryBody | ConvertTo-Json -Depth 10

Write-Host "`n[11] Retention dry run" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/security/retention/run?tenant_id=$TenantId&days_to_keep=90&dry_run=true" -Method POST -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "`n[12] Security audit events" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/security/audit/events?tenant_id=$TenantId&limit=20" -Headers $Headers | ConvertTo-Json -Depth 20

Write-Host "`n[13] Final Phase 4 health" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/v1/phase4/health?tenant_id=$TenantId" -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "`nOpen SOC console:" -ForegroundColor Green
Write-Host "$BaseUrl/soc"
