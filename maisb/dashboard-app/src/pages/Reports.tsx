import { useState } from 'react'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest, downloadWithAuth } from '../lib/api'

export default function Reports() {
  const [message, setMessage] = useState('')

  async function generateCompliance() {
    setMessage('')
    try {
      const data = await apiRequest<{ report_id: string; status: string }>('/v1/reports/compliance', {
        method: 'POST',
        body: JSON.stringify({ framework: 'soc2' }),
      })
      setMessage(`Compliance report ${data.report_id} is ${data.status}.`)
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <main className="stack">
      <h1>Reports</h1>
      <Card title="Exports">
        <div className="row-inline">
          <Button variant="secondary" onClick={() => downloadWithAuth('/v1/reports/export.csv', 'maisb-report.csv')}>Export CSV</Button>
          <Button variant="secondary" onClick={() => downloadWithAuth('/v1/reports/export.json', 'maisb-report.json')}>Export JSON</Button>
          <Button onClick={generateCompliance}>Generate compliance report</Button>
        </div>
      </Card>
      <Card title="Schedule report">
        <p className="muted">Scheduling placeholder: workflow configuration and delivery channels are being finalized.</p>
      </Card>
      {message && <p className="notice">{message}</p>}
    </main>
  )
}
