import { useEffect, useState } from 'react'
import Badge from '../components/Badge'
import ChartCard from '../components/ChartCard'
import Button from '../components/Button'
import { apiRequest } from '../lib/api'
import { SAMPLE_DECISION_BREAKDOWN, SAMPLE_RISK_DISTRIBUTION, SAMPLE_SCANS_OVER_TIME, SAMPLE_TOP_CHANNELS } from '../lib/dashboard'

type ScansResponse = { points: Array<{ date: string; count: number }> }
type DecisionsResponse = { decisions: Record<string, number> }
type RiskResponse = { distribution: Record<string, number> }
type TopChannelsResponse = { channels: Array<{ channel: string; count: number; avg_risk: number }> }

export default function Analytics() {
  const [range, setRange] = useState<'weekly' | 'monthly'>('weekly')
  const [scans, setScans] = useState(SAMPLE_SCANS_OVER_TIME)
  const [decisions, setDecisions] = useState(SAMPLE_DECISION_BREAKDOWN)
  const [riskDistribution, setRiskDistribution] = useState(SAMPLE_RISK_DISTRIBUTION)
  const [topChannels, setTopChannels] = useState(SAMPLE_TOP_CHANNELS)
  const [sampleFlags, setSampleFlags] = useState({ scans: true, decisions: true, risk: true, channels: true })

  useEffect(() => {
    Promise.all([
      apiRequest<ScansResponse>(`/v1/dashboard/analytics/scans-over-time?range=${range}`),
      apiRequest<DecisionsResponse>('/v1/dashboard/analytics/decision-breakdown'),
      apiRequest<RiskResponse>('/v1/dashboard/analytics/risk-distribution'),
      apiRequest<TopChannelsResponse>('/v1/dashboard/analytics/top-risk-channels'),
    ])
      .then(([scanData, decisionData, riskData, channelData]) => {
        if (scanData.points?.length) {
          setScans(scanData.points)
          setSampleFlags((flag) => ({ ...flag, scans: false }))
        }
        if (decisionData.decisions && Object.values(decisionData.decisions).some((value) => value > 0)) {
          setDecisions(decisionData.decisions as typeof SAMPLE_DECISION_BREAKDOWN)
          setSampleFlags((flag) => ({ ...flag, decisions: false }))
        }
        if (riskData.distribution && Object.values(riskData.distribution).some((value) => value > 0)) {
          setRiskDistribution(riskData.distribution as typeof SAMPLE_RISK_DISTRIBUTION)
          setSampleFlags((flag) => ({ ...flag, risk: false }))
        }
        if (channelData.channels?.length) {
          setTopChannels(channelData.channels)
          setSampleFlags((flag) => ({ ...flag, channels: false }))
        }
      })
      .catch(() => undefined)
  }, [range])

  const scanMax = Math.max(...scans.map((item) => item.count), 1)

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Security analytics</p>
          <h1>Analytics</h1>
          <p className="muted">Gradient charts summarize boundary activity across the current window.</p>
        </div>
        <div className="row-inline">
          <Button variant={range === 'weekly' ? 'primary' : 'secondary'} onClick={() => setRange('weekly')}>Weekly</Button>
          <Button variant={range === 'monthly' ? 'primary' : 'secondary'} onClick={() => setRange('monthly')}>Monthly</Button>
        </div>
      </div>

      <div className="grid two-col">
        <ChartCard title="Scans over time" sampleData={sampleFlags.scans}>
          {scans.map((point) => (
            <div key={point.date} className="bar-row">
              <span>{point.date}</span>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${(point.count / scanMax) * 100}%` }} /></div>
              <strong>{point.count}</strong>
            </div>
          ))}
        </ChartCard>

        <ChartCard title="Decision breakdown" sampleData={sampleFlags.decisions}>
          {Object.entries(decisions).map(([label, value]) => (
            <div key={label} className="split-row">
              <span>{label}</span>
              <Badge>{value}</Badge>
            </div>
          ))}
        </ChartCard>

        <ChartCard title="Risk score distribution" sampleData={sampleFlags.risk}>
          {Object.entries(riskDistribution).map(([label, value]) => (
            <div key={label} className="bar-row">
              <span>{label}</span>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, value)}%` }} /></div>
              <strong>{value}</strong>
            </div>
          ))}
        </ChartCard>

        <ChartCard title="Top risk channels" sampleData={sampleFlags.channels}>
          {topChannels.map((item) => (
            <div key={item.channel} className="split-row">
              <span>{item.channel}</span>
              <Badge>{item.avg_risk.toFixed(2)} risk · {item.count} scans</Badge>
            </div>
          ))}
        </ChartCard>
      </div>
    </main>
  )
}
