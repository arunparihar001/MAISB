import { useState } from 'react'
import type { FormEvent } from 'react'
import CertifyBadge from '../components/CertifyBadge'
import { apiRequest } from '../lib/api'
import { getApiKey } from '../lib/auth'

type StartResponse = {
  order_id: string
  report_pdf_url: string
  badge_svg_url: string
  status: string
}

type OrderResponse = {
  report?: { grade?: string }
}

export default function Certify() {
  const [form, setForm] = useState({ email: '', company: '', package: 'standard', target_type: 'mobile_ai_agent', notes: '' })
  const [result, setResult] = useState<StartResponse | null>(null)
  const [grade, setGrade] = useState('')
  const [error, setError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      const start = await apiRequest<StartResponse>('/v1/commercial/certify/start', {
        method: 'POST',
        body: { ...form, api_key: getApiKey() },
      })
      setResult(start)
      const order = await apiRequest<OrderResponse>(`/v1/commercial/certify/orders/${start.order_id}`)
      setGrade(order.report?.grade ? `Grade ${order.report.grade}` : '')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not create certify order')
    }
  }

  return (
    <section className="stack">
      <h1>MAISB Certify</h1>
      <form className="card form" onSubmit={submit}>
        <label>Email</label>
        <input required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label>Company</label>
        <input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <label>Package</label>
        <select value={form.package} onChange={(e) => setForm({ ...form, package: e.target.value })}>
          <option value="starter">starter</option>
          <option value="standard">standard</option>
          <option value="enterprise">enterprise</option>
        </select>
        <label>Target Type</label>
        <input value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value })} />
        <label>Notes</label>
        <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <button className="btn" type="submit">Start assessment</button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      {result ? (
        <section className="card">
          <p>Order: <span className="mono">{result.order_id}</span></p>
          <p>Status: {result.status}</p>
          {grade ? <p>{grade}</p> : null}
          <div className="row">
            <a className="btn secondary" href={result.report_pdf_url} target="_blank" rel="noreferrer">Download report PDF</a>
            <a className="btn secondary" href={result.badge_svg_url} target="_blank" rel="noreferrer">View badge SVG</a>
          </div>
          <CertifyBadge badgeUrl={result.badge_svg_url} />
        </section>
      ) : null}
    </section>
  )
}
