import { useState } from 'react'
import CertifyBadge from '../components/CertifyBadge'
import { apiRequest } from '../lib/api'
import { getApiKey } from '../lib/auth'

type CertifyResponse = {
  order_id: string
  payment_status: string
}

export default function Certify() {
  const [orderId, setOrderId] = useState('')
  const [error, setError] = useState('')
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')

  const start = async () => {
    setError('')
    if (!email.trim() || !company.trim()) {
      setError('Email and company are required')
      return
    }
    try {
      const response = await apiRequest<CertifyResponse>('/v1/commercial/certify/start', {
        method: 'POST',
        body: JSON.stringify({
          email,
          company,
          api_key: getApiKey(),
          package: 'standard',
          target_type: 'mobile_ai_agent',
        }),
      })
      setOrderId(response.order_id)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="stack">
      <h2>Certify</h2>
      <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
      <input value={company} onChange={(event) => setCompany(event.target.value)} placeholder="Company" />
      <CertifyBadge grade={orderId ? 'Requested' : undefined} />
      <button type="button" onClick={start}>Start assessment</button>
      {orderId && <p>Order: {orderId}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  )
}
