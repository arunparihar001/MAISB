import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import RiskQueueTable from '../components/RiskQueueTable'

export default function SocConsole() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([])
  useEffect(() => {
    Promise.all([
      apiGet<{ items?: Array<Record<string, unknown>>; queue?: Array<Record<string, unknown>> }>('/v1/soc/risk-queue').catch(() => ({ items: [] })),
      apiGet<{ cases?: Array<Record<string, unknown>> }>('/v1/soc/cases').catch(() => ({ cases: [] })),
    ]).then(([queueData, cases]) => {
      const queue = queueData as { items?: Array<Record<string, unknown>>; queue?: Array<Record<string, unknown>> }
      setRows([...(queue.items || queue.queue || []), ...(cases.cases || [])])
    })
  }, [])
  return <main className="page"><h1>SOC Console (Admin)</h1><RiskQueueTable rows={rows} /></main>
}
