import { useState } from 'react'
import MetricCard from '../components/MetricCard'
import RiskQueueTable, { RiskRow } from '../components/RiskQueueTable'
import { adminHeaders, apiRequest, withAdminKey } from '../lib/api'
import { getAdminKey, setAdminKey } from '../lib/auth'

type AnyRecord = Record<string, unknown>

function normalizeRows(items: AnyRecord[] = [], type: string): RiskRow[] {
  return items.map((item, index) => ({
    id: String(item.id || item.case_id || item.trace_id || item.request_id || item.order_id || `${type}-${index + 1}`),
    type,
    status: String(item.status || item.decision || item.state || 'open'),
    severity: String(item.severity || item.risk || item.risk_score || '—'),
    created: String(item.created || item.created_at || item.ts || item.timestamp || '—'),
  }))
}

export default function SocConsole() {
  const [adminKey, setAdminKeyInput] = useState(getAdminKey())
  const [riskRows, setRiskRows] = useState<RiskRow[]>([])
  const [caseRows, setCaseRows] = useState<RiskRow[]>([])
  const [commercialRows, setCommercialRows] = useState<RiskRow[]>([])
  const [summary, setSummary] = useState<AnyRecord | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setError('')
    if (!adminKey.trim()) { setError('Admin key is required for SOC access.'); return }
    setAdminKey(adminKey.trim()); setLoading(true)
    try {
      const headers = adminHeaders(adminKey)
      const [risk, cases, dash, commercial] = await Promise.allSettled([
        apiRequest<AnyRecord>(withAdminKey('/v1/soc/risk-queue', adminKey), { headers }),
        apiRequest<AnyRecord>(withAdminKey('/v1/soc/cases', adminKey), { headers }),
        apiRequest<AnyRecord>(withAdminKey('/v1/dashboard/summary', adminKey), { headers }),
        apiRequest<AnyRecord>(withAdminKey('/v1/commercial/admin/requests', adminKey), { headers }),
      ])
      if (risk.status === 'fulfilled') setRiskRows(normalizeRows((risk.value.items || risk.value.queue || risk.value.risk_queue || []) as AnyRecord[], 'risk'))
      if (cases.status === 'fulfilled') setCaseRows(normalizeRows((cases.value.cases || cases.value.items || []) as AnyRecord[], 'case'))
      if (dash.status === 'fulfilled') setSummary(dash.value)
      if (commercial.status === 'fulfilled') {
        const billing = (commercial.value.billing_requests || []) as AnyRecord[]
        const certs = (commercial.value.certify_orders || []) as AnyRecord[]
        setCommercialRows([...normalizeRows(billing, 'billing_request'), ...normalizeRows(certs, 'certify_order')])
      }
      const failures = [risk, cases, dash].filter((x) => x.status === 'rejected')
      if (failures.length >= 3) setError('SOC endpoints could not be loaded. Check admin key and backend route availability.')
    } catch (err) { setError((err as Error).message) } finally { setLoading(false) }
  }

  return <div className="stack"><h2>SOC dashboard</h2><div className="card form-grid"><input type="password" value={adminKey} onChange={(e) => setAdminKeyInput(e.target.value)} placeholder="Admin key" /><button type="button" onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Load SOC data'}</button></div>{error && <p className="error">{error}</p>}{loading && <div className="card"><p>Loading SOC data...</p></div>}{summary && <div className="grid"><MetricCard title="Summary keys" value={Object.keys(summary).length} /><MetricCard title="Risk rows" value={riskRows.length} /><MetricCard title="Cases" value={caseRows.length} /></div>}<RiskQueueTable title="Phase 4 Risk Queue" rows={riskRows} /><RiskQueueTable title="SOC Cases" rows={caseRows} /><RiskQueueTable title="Commercial Admin Requests" rows={commercialRows} /></div>
}
