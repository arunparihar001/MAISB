import Badge from './Badge'
import Card from './Card'

type Props = {
  channel: string
  status: string
  scans: number
  blocked: number
  reputation: number
}

export default function BoundaryCard({ channel, status, scans, blocked, reputation }: Props) {
  return (
    <Card title={channel}>
      <div className="split-row"><span className="muted">Status</span><Badge>{status}</Badge></div>
      <div className="split-row"><span className="muted">Scans</span><strong>{scans}</strong></div>
      <div className="split-row"><span className="muted">Blocked</span><strong>{blocked}</strong></div>
      <div className="split-row"><span className="muted">Reputation</span><strong>{Math.round(reputation * 100)}%</strong></div>
    </Card>
  )
}
