# PHASE 3 TEST COMMANDS - FIXED VERSION
# Run these after:
# cd E:\projects\maisb-monorepo\maisb\llm_proxy
# .\.venv\Scripts\Activate.ps1
# uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload

$BaseUrl = "http://127.0.0.1:8001"
$TenantId = "default"
$AdminKey = "change_me_in_production"
$WindowHours = 24

function Show-Section($Title) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Invoke-Json($Url, $Depth = 10) {
    Write-Host "GET $Url" -ForegroundColor DarkGray
    Invoke-RestMethod -Uri $Url | ConvertTo-Json -Depth $Depth
}

# 1) Phase 3 health
Show-Section "1) Phase 3 Health"
Invoke-Json -Url ("{0}/v1/phase3/health" -f $BaseUrl) -Depth 10

# 2) Dashboard summary
Show-Section "2) Dashboard Summary"
Invoke-Json -Url ("{0}/v1/dashboard/summary?tenant_id={1}&hours={2}&admin_key={3}" -f $BaseUrl, $TenantId, $WindowHours, $AdminKey) -Depth 20

# 3) Decision summary
Show-Section "3) Decision Summary"
Invoke-Json -Url ("{0}/v1/dashboard/decisions?tenant_id={1}&hours={2}&admin_key={3}" -f $BaseUrl, $TenantId, $WindowHours, $AdminKey) -Depth 10

# 4) Channel reputation dashboard data
Show-Section "4) Channel Reputation Dashboard Data"
Invoke-Json -Url ("{0}/v1/dashboard/channels?tenant_id={1}&hours={2}&admin_key={3}" -f $BaseUrl, $TenantId, $WindowHours, $AdminKey) -Depth 20

# 5) Timeline
Show-Section "5) Timeline"
Invoke-Json -Url ("{0}/v1/dashboard/timeline?tenant_id={1}&limit=25&admin_key={2}" -f $BaseUrl, $TenantId, $AdminKey) -Depth 20

# 6) Recent traces
Show-Section "6) Recent Traces"
$recentUrl = "{0}/v1/dashboard/recent-traces?tenant_id={1}&limit=5&admin_key={2}" -f $BaseUrl, $TenantId, $AdminKey
Write-Host "GET $recentUrl" -ForegroundColor DarkGray
$recent = Invoke-RestMethod -Uri $recentUrl
$recent | ConvertTo-Json -Depth 30

# 7) Trace graph for first recent trace if available
Show-Section "7) Trace Graph For First Recent Trace"

$traceList = @($recent.traces)

if ($traceList.Count -gt 0) {
    $traceId = $traceList[0].trace_id
    Write-Host "Using trace_id: $traceId" -ForegroundColor Yellow

    # IMPORTANT:
    # Use -f formatting instead of direct "$traceId?tenant_id=..." interpolation.
    # This avoids PowerShell query-string parsing issues.
    $traceGraphUrl = "{0}/v1/dashboard/trace-graph/{1}?tenant_id={2}&admin_key={3}" -f $BaseUrl, $traceId, $TenantId, $AdminKey

    Invoke-Json -Url $traceGraphUrl -Depth 30
}
else {
    Write-Host "No recent traces found. Skipping trace graph test." -ForegroundColor Yellow
}

# 8) Export JSON
Show-Section "8) Export JSON"
Invoke-Json -Url ("{0}/v1/dashboard/export?tenant_id={1}&format=json&limit=20&admin_key={2}" -f $BaseUrl, $TenantId, $AdminKey) -Depth 20

# 9) Create an incident from a recent trace if available
Show-Section "9) Create Incident From Recent Trace"

if ($traceList.Count -gt 0) {
    $incidentBody = @{
        tenant_id = $TenantId
        trace_id = $traceList[0].trace_id
        severity = "high"
        title = "Blocked high-risk prompt injection trace"
        details = @{
            source = "phase3_test"
            note = "Created from Phase 3 dashboard test script"
        }
    } | ConvertTo-Json -Depth 10

    $incidentUrl = "{0}/v1/dashboard/incidents?admin_key={1}" -f $BaseUrl, $AdminKey

    Write-Host "POST $incidentUrl" -ForegroundColor DarkGray

    Invoke-RestMethod `
        -Uri $incidentUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $incidentBody |
        ConvertTo-Json -Depth 10
}
else {
    Write-Host "No recent traces found. Skipping incident creation." -ForegroundColor Yellow
}

# 10) Verify Phase 3 health again after incident creation
Show-Section "10) Phase 3 Health After Incident Test"
Invoke-Json -Url ("{0}/v1/phase3/health" -f $BaseUrl) -Depth 10

# 11) Dashboard URL
Show-Section "11) Dashboard URL"
Write-Host "Open this in browser:" -ForegroundColor Green
Write-Host "$BaseUrl/dashboard" -ForegroundColor Green

# Optional: automatically open dashboard
# Start-Process "$BaseUrl/dashboard"

Write-Host ""
Write-Host "Phase 3 test script completed." -ForegroundColor Green
