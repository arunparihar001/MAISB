import { FormEvent, useState } from 'react'
import CertifyBadge from '../components/CertifyBadge'
import { apiRequest } from '../lib/api'
import { API_BASE_URL } from '../lib/config'
import { getApiKey } from '../lib/auth'

type CertifyResponse = { order_id: string; status?: string; payment_status?: string; report?: { grade?: string } }

export default function Certify() {
  const [form, setForm] = useState({ email: '', company: '', package: 'standard', target_type: 'mobile_ai_agent', notes: '' })
  const [order, setOrder] = useState<CertifyResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function start(event: FormEvent) {
    event.preventDefault(); setError(''); setLoading(true)
    if (!form.email.trim() || !form.company.trim()) { setError('Email and company are required'); setLoading(false); return }
    try {
      const response = await apiRequest<CertifyResponse>('/v1/commercial/certify/start', { method: 'POST', body: JSON.stringify({ ...form, api_key: getApiKey() }) })
      setOrder(response)
    } catch (err) { setError((err as Error).message) } finally { setLoading(false) }
  }

  return <div className="stack"><h2>MAISB Certify</h2><form onSubmit={start} className="card form-grid"><input required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" /><input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="Company" /><input value={form.package} onChange={(e) => setForm({ ...form, package: e.target.value })} placeholder="Package" /><input value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value })} placeholder="Target type" /><textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Assessment notes" /><button type="submit" disabled={loading}>{loading ? 'Starting…' : 'Start assessment'}</button></form>{error && <p className="error">{error}</p>}{order && <div className="card"><CertifyBadge grade={order.report?.grade || order.status || order.payment_status} orderId={order.order_id} /><p>Order: <code>{order.order_id}</code></p><p>Status: {order.status || order.payment_status || 'requested'}</p><p><a href={`${API_BASE_URL}/v1/commercial/certify/orders/${order.order_id}/report.pdf`} target="_blank">Report PDF</a> · <a href={`${API_BASE_URL}/v1/commercial/certify/orders/${order.order_id}/badge.svg`} target="_blank">Badge SVG</a></p></div>}</div>
}
