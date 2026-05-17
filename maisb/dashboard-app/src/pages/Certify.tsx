import { useState } from 'react'
import { apiGet, apiPost } from '../lib/api'
import CertifyBadge from '../components/CertifyBadge'
import { API_BASE_URL } from '../lib/config'

export default function Certify() {
  const [orderId, setOrderId] = useState('')
  const [grade, setGrade] = useState('')
  const [message, setMessage] = useState('')
  const start = async () => {
    const d = await apiPost<{ order_id: string }>('/v1/commercial/certify/start', { email: 'customer@example.com', company: 'Customer Inc' })
    setOrderId(d.order_id)
    setMessage('Certify order created.')
  }
  const check = async () => {
    if (!orderId) return
    const d = await apiGet<{ report: { grade: string } }>(`/v1/commercial/certify/orders/${orderId}`)
    setGrade(d.report.grade)
  }
  return <main className="page"><h1>Certify</h1><button onClick={start}>Start Certify</button><button onClick={check}>Check Order</button>{orderId && <p>Order: {orderId}</p>}<CertifyBadge grade={grade} /><p>{message}</p>{orderId && <p><a href={`${API_BASE_URL}/v1/commercial/certify/orders/${orderId}/report.pdf`}>Report PDF</a> · <a href={`${API_BASE_URL}/v1/commercial/certify/orders/${orderId}/badge.svg`}>Badge</a></p>}</main>
}
