import { useState } from 'react'
import RiskQueueTable from '../components/RiskQueueTable'
import { apiRequest } from '../lib/api'
import { getAdminKey, setAdminKey } from '../lib/auth'

type AdminRequestsResponse = {
  billing_requests: Array<{ request_id: string; status: string; created_at: string }>
  certify_orders: Array<{ order_id: string; status: string; created: string }>
}

export default function SocConsole() {
  const [adminKey, setAdminKeyInput] = useState(getAdminKey())
  const [rows, setRows] = useState<Array<{ id: string; status: string; type: string; created: string }>>([])
  const [error, setError] = useState('')

  const load = async () => {
    setError('')
    if (!adminKey.trim()) {
      setError('Admin key is required for SOC access')
      return
    }
    setAdminKey(adminKey)
    try {
      const data = await apiRequest<AdminRequestsResponse>('/v1/commercial/admin/requests', {
        headers: { Authorization: `Bearer ${adminKey}` },
      })
      const billingRows = data.billing_requests.map((item) => ({
        id: item.request_id,
        status: item.status,
        type: 'billing_request',
        created: item.created_at,
      }))
      const certifyRows = data.certify_orders.map((item) => ({
        id: item.order_id,
        status: item.status,
        type: 'certify_order',
        created: item.created,
      }))
      setRows([...billingRows, ...certifyRows])
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="stack">
      <h2>SOC Console</h2>
      <input value={adminKey} onChange={(event) => setAdminKeyInput(event.target.value)} placeholder="Admin key" />
      <button type="button" onClick={load}>Load SOC queue</button>
      {error && <p className="error">{error}</p>}
      <RiskQueueTable rows={rows} />
    </div>
  )
}
