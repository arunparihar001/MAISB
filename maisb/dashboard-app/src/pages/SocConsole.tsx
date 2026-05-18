import { FormEvent, useState } from 'react'
import RiskQueueTable from '../components/RiskQueueTable'
import { apiRequest } from '../lib/api'
import { getAdminKey } from '../lib/auth'

interface RiskResponse {
  items: Array<{ event_id?: string; trace_id?: string; channel?: string; decision?: string; risk_score?: number }>
}

interface CasesResponse {
  cases: Array<{ case_id: string; severity: string; status: string; owner?: string; title: string }>
}

export default function SocConsole() {
  const [tenantId, setTenantId] = useState('default')
  const [risk, setRisk] = useState<RiskResponse['items']>([])
  const [cases, setCases] = useState<CasesResponse['cases']>([])
  const [error, setError] = useState('')

  async function loadSoc(event?: FormEvent) {
    event?.preventDefault()
    const adminKey = getAdminKey()
    if (!adminKey) {
      setError('Set admin key in Settings to access SOC endpoints')
      return
    }
    try {
      const [riskData, caseData] = await Promise.all([
        apiRequest<RiskResponse>(`/v1/soc/risk-queue?tenant_id=${encodeURIComponent(tenantId)}`, {}, adminKey),
        apiRequest<CasesResponse>(`/v1/soc/cases?tenant_id=${encodeURIComponent(tenantId)}`, {}, adminKey),
      ])
      setRisk(riskData.items)
      setCases(caseData.cases)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SOC load failed')
    }
  }

  return (
    <div className="page-grid">
      <form className="card form" onSubmit={loadSoc}>
        <h3>SOC Console</h3>
        <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
        <button type="submit">Refresh SOC Data</button>
        {error && <p className="error">{error}</p>}
      </form>
      <RiskQueueTable items={risk} />
      <div className="card">
        <h3>Cases</h3>
        <table>
          <thead><tr><th>Case</th><th>Title</th><th>Severity</th><th>Status</th><th>Owner</th></tr></thead>
          <tbody>
            {cases.slice(0, 10).map((item) => (
              <tr key={item.case_id}>
                <td>{item.case_id}</td><td>{item.title}</td><td>{item.severity}</td><td>{item.status}</td><td>{item.owner || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
