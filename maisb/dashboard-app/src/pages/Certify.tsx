import { FormEvent, useState } from 'react'
import CertifyBadge from '../components/CertifyBadge'
import { apiRequest } from '../lib/api'
import { getApiKey } from '../lib/auth'

interface CertifyResponse {
  order_id: string
  status: string
  report_pdf_url: string
  badge_svg_url: string
}

export default function Certify() {
  const [form, setForm] = useState({ email: '', company: '', package: 'standard', target_type: 'mobile_ai_agent', notes: '' })
  const [order, setOrder] = useState<CertifyResponse | null>(null)
  const [status, setStatus] = useState('')

  async function startCertify(event: FormEvent) {
    event.preventDefault()
    setStatus('')
    try {
      const result = await apiRequest<CertifyResponse>('/v1/commercial/certify/start', {
        method: 'POST',
        body: JSON.stringify({ ...form, api_key: getApiKey() || null }),
      })
      setOrder(result)
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Unable to start certify')
    }
  }

  return (
    <div className="page-grid">
      <form className="card form" onSubmit={startCertify}>
        <h3>Start MAISB Certify</h3>
        <input placeholder="Security contact email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input placeholder="Company" required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <select value={form.package} onChange={(e) => setForm({ ...form, package: e.target.value })}>
          <option value="starter">Starter</option>
          <option value="standard">Standard</option>
          <option value="enterprise">Enterprise</option>
        </select>
        <input placeholder="Target type" value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value })} />
        <textarea placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <button type="submit">Create order</button>
        {status && <p className="error">{status}</p>}
      </form>
      {order && (
        <div className="card">
          <h3>Order {order.order_id}</h3>
          <p>Status: {order.status}</p>
          <a href={order.report_pdf_url} target="_blank" rel="noreferrer">Download report PDF</a>
          <CertifyBadge badgeUrl={order.badge_svg_url} />
        </div>
      )}
    </div>
  )
}
