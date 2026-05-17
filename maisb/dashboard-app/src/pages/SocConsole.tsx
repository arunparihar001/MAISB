import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import RiskQueueTable from '../components/RiskQueueTable'
import { getAdminKey, setAdminKey } from '../lib/auth'

export default function SocConsole() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([])
  const [adminKeyInput, setAdminKeyInput] = useState(getAdminKey())
  const [error, setError] = useState('')

  const loadSocData = async (adminKey: string) => {
    if (!adminKey.trim()) {
      setError('Admin key is required to load SOC risk queue and cases.')
      setRows([])
      return
    }

    setError('')
    setAdminKey(adminKey)

    try {
      const headers = { Authorization: `Bearer ${adminKey}` }
      const [queueData, cases] = await Promise.all([
        apiGet<{ items?: Array<Record<string, unknown>>; queue?: Array<Record<string, unknown>> }>('/v1/soc/risk-queue', { admin_key: adminKey }, headers),
        apiGet<{ cases?: Array<Record<string, unknown>> }>('/v1/soc/cases', { admin_key: adminKey }, headers),
      ])
      const queue = queueData as { items?: Array<Record<string, unknown>>; queue?: Array<Record<string, unknown>> }
      setRows([...(queue.items || queue.queue || []), ...(cases.cases || [])])
    } catch {
      setError('Failed to load SOC data. Verify the admin key and try again.')
      setRows([])
    }
  }

  useEffect(() => {
    const savedAdminKey = getAdminKey()
    if (savedAdminKey) {
      setAdminKeyInput(savedAdminKey)
      loadSocData(savedAdminKey)
    } else {
      setError('Admin key is required to load SOC risk queue and cases.')
    }
  }, [])

  return (
    <main className="page">
      <h1>SOC Console (Admin)</h1>
      <p>Use an admin key to access risk queue and case management endpoints.</p>
      <div>
        <input
          value={adminKeyInput}
          onChange={(e) => setAdminKeyInput(e.target.value)}
          placeholder="Admin key"
          type="password"
        />
        <button onClick={() => loadSocData(adminKeyInput)}>Load SOC Data</button>
      </div>
      {error && <p className="error-text">{error}</p>}
      <RiskQueueTable rows={rows} />
    </main>
  )
}
