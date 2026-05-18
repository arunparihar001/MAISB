import { useState } from 'react'
import type { FormEvent } from 'react'
import RiskQueueTable from '../components/RiskQueueTable'
import { apiRequest } from '../lib/api'
import { getAdminKey, setAdminKey } from '../lib/auth'

type RiskResponse = { items: Array<{ trace_id?: string; event_id?: string; decision?: string; risk_score?: number; created_at?: string; channel?: string }> }
type CasesResponse = { cases: Array<{ case_id: string; title: string; status: string; severity: string; risk_score: number }> }

export default function SocConsole() {
  const [adminKey, setLocalAdminKey] = useState(getAdminKey())
  const [risk, setRisk] = useState<RiskResponse | null>(null)
  const [cases, setCases] = useState<CasesResponse | null>(null)
  const [error, setError] = useState('')

  const loadData = async (event?: FormEvent) => {
    event?.preventDefault()
    setError('')
    try {
      setAdminKey(adminKey)
      const headers = adminKey ? { Authorization: `Bearer ${adminKey}` } : undefined
      const [riskResponse, casesResponse] = await Promise.all([
        apiRequest<RiskResponse>('/v1/soc/risk-queue', { headers }),
        apiRequest<CasesResponse>('/v1/soc/cases', { headers }),
      ])
      setRisk(riskResponse)
      setCases(casesResponse)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'SOC load failed')
    }
  }

  return (
    <section className="stack">
      <h1>SOC Console</h1>
      <form className="card form" onSubmit={loadData}>
        <label>Admin Bearer Key</label>
        <input value={adminKey} onChange={(e) => setLocalAdminKey(e.target.value)} placeholder="Paste ADMIN_KEY" />
        <button className="btn" type="submit">Load SOC data</button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <RiskQueueTable items={risk?.items || []} />
      <section className="card">
        <h3>Cases</h3>
        <table className="table">
          <thead><tr><th>Case</th><th>Title</th><th>Status</th><th>Severity</th><th>Risk</th></tr></thead>
          <tbody>
            {(cases?.cases || []).map((item) => (
              <tr key={item.case_id}><td>{item.case_id}</td><td>{item.title}</td><td>{item.status}</td><td>{item.severity}</td><td>{item.risk_score}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
