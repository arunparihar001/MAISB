import { useState } from 'react'
import { apiGet, apiPost } from '../lib/api'
import CertifyBadge from '../components/CertifyBadge'
import { API_BASE_URL } from '../lib/config'

type CertifyPackage = 'starter' | 'standard' | 'enterprise'

export default function Certify() {
  const [orderId, setOrderId] = useState('')
  const [grade, setGrade] = useState('')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')
  const [pkg, setPkg] = useState<CertifyPackage>('standard')
  const [targetType, setTargetType] = useState('mobile_ai_agent')
  const [notes, setNotes] = useState('')

  const start = async () => {
    if (!email.trim() || !company.trim()) {
      setMessage('Email and company are required to start a Certify order.')
      return
    }

    try {
      const d = await apiPost<{ order_id: string }>('/v1/commercial/certify/start', {
        email,
        company,
        package: pkg,
        target_type: targetType,
        notes,
      })
      setOrderId(d.order_id)
      setMessage('Certify order created.')
    } catch {
      setMessage('Unable to start certify order. Please verify the fields and try again.')
    }
  }

  const check = async () => {
    if (!orderId) return
    try {
      const d = await apiGet<{ report: { grade: string } }>(`/v1/commercial/certify/orders/${orderId}`)
      setGrade(d.report.grade)
    } catch {
      setMessage('Unable to fetch certify order status.')
    }
  }

  return (
    <main className="page">
      <h1>MAISB Certify</h1>
      <p>Submit assessment details to create a certify order and track report readiness.</p>

      <div className="grid">
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Customer email" />
        <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company name" />
        <select value={pkg} onChange={(e) => setPkg(e.target.value as CertifyPackage)}>
          <option value="starter">Starter</option>
          <option value="standard">Standard</option>
          <option value="enterprise">Enterprise</option>
        </select>
        <input value={targetType} onChange={(e) => setTargetType(e.target.value)} placeholder="Target type (e.g. mobile_ai_agent)" />
      </div>

      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Assessment notes" rows={4} />

      <div>
        <button onClick={start}>Start Certify</button>
        <button onClick={check}>Check Order</button>
      </div>

      {orderId && <p>Order: {orderId}</p>}
      <CertifyBadge grade={grade} />
      <p>{message}</p>
      {orderId && (
        <p>
          <a href={`${API_BASE_URL}/v1/commercial/certify/orders/${orderId}/report.pdf`}>Report PDF</a>
          {' · '}
          <a href={`${API_BASE_URL}/v1/commercial/certify/orders/${orderId}/badge.svg`}>Badge</a>
        </p>
      )}
    </main>
  )
}
