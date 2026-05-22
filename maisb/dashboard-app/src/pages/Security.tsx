import { useEffect, useState } from 'react'
import Card from '../components/Card'
import DataTable from '../components/DataTable'
import { apiRequest } from '../lib/api'

type RiskTimelinePoint = { created_at: string; risk_score: number; decision: string }
type SecurityEvent = {
  created_at: string
  channel: string
  decision: string
  risk_score: number
  taxonomy_class: string
  trace_id: string
  payload_hash?: string | null
  redacted_preview?: string | null
}

export default function Security() {
  const [timeline, setTimeline] = useState<RiskTimelinePoint[]>([])
  const [events, setEvents] = useState<SecurityEvent[]>([])

  useEffect(() => {
    Promise.all([
      apiRequest<{ timeline: RiskTimelinePoint[] }>('/v1/dashboard/security/risk-timeline?range=weekly'),
      apiRequest<{ items: SecurityEvent[] }>('/v1/dashboard/security/blocked-payloads'),
    ])
      .then(([timelineData, eventData]) => {
        setTimeline(timelineData.timeline || [])
        setEvents(eventData.items || [])
      })
      .catch(() => {
        setTimeline([])
        setEvents([])
      })
  }, [])

  return (
    <main className="stack">
      <h1>Security Events</h1>
      <Card title="Risk timeline">
        <div className="timeline-risk">
          {timeline.slice(-20).map((point) => (
            <div key={`${point.created_at}-${point.risk_score}`} className="risk-dot" style={{ height: `${20 + point.risk_score * 90}px` }} title={`${point.decision} ${point.risk_score}`} />
          ))}
        </div>
      </Card>

      <Card title="Recent blocked/reviewed events">
        <DataTable
          columns={[
            { key: 'time', label: 'Time', render: (row) => row.created_at },
            { key: 'channel', label: 'Channel', render: (row) => row.channel },
            { key: 'decision', label: 'Decision', render: (row) => row.decision },
            { key: 'risk', label: 'Risk Score', render: (row) => Number(row.risk_score || 0).toFixed(2) },
            { key: 'taxonomy', label: 'Taxonomy', render: (row) => row.taxonomy_class || '—' },
            { key: 'trace', label: 'Trace ID', render: (row) => row.trace_id || '—' },
            {
              key: 'action',
              label: 'Action',
              render: (row) => row.redacted_preview || row.payload_hash || 'Redacted preview unavailable',
            },
          ]}
          rows={events}
          rowKey={(row, index) => `${row.trace_id}-${index}`}
        />
      </Card>
    </main>
  )
}
