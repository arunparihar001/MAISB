import { useEffect, useState } from 'react'
import Card from '../components/Card'
import TraceTimeline from '../components/TraceTimeline'
import { apiRequest } from '../lib/api'

type Trace = {
  trace_id: string
  channels: string[]
  trust_score?: number
  trust_degradation?: number
  degradation_score?: number
  final_decision?: string
  created_at?: string
}

export default function Traces() {
  const [traces, setTraces] = useState<Trace[]>([])

  useEffect(() => {
    apiRequest<{ traces: Trace[] }>('/v1/dashboard/traces')
      .then((data) => setTraces(data.traces || []))
      .catch(() => setTraces([]))
  }, [])

  return (
    <main className="stack">
      <h1>Cross-Channel Trace</h1>
      <Card>
        <p className="muted">Single-channel tools miss attacks that become dangerous across mobile context. MAISB tracks cross-channel behavior before the LLM acts.</p>
      </Card>
      <TraceTimeline traces={traces.slice(0, 20)} />
    </main>
  )
}
