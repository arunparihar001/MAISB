import LandingSection from './LandingSection'

const SCAN_BARS = [42, 58, 45, 72, 68, 85, 78, 92, 88, 95, 82, 76]
const RISK_DOTS = [28, 42, 35, 58, 72, 65, 88, 76, 92, 84, 68, 55, 48, 62]

const BLOCKED_ROWS = [
  { time: '14:32', channel: 'Clipboard', score: '0.94', trace: 'trace_q9z4' },
  { time: '14:18', channel: 'QR Code', score: '0.87', trace: 'trace_m2k8p' },
  { time: '13:55', channel: 'Deep Link', score: '0.91', trace: 'trace_x7n1w' },
]

const CHANNELS = [
  { name: 'Clipboard', score: 82, status: 'elevated' },
  { name: 'QR Code', score: 67, status: 'moderate' },
  { name: 'Notification', score: 34, status: 'low' },
  { name: 'Deep Link', score: 71, status: 'moderate' },
  { name: 'Share Intent', score: 45, status: 'low' },
  { name: 'NFC', score: 58, status: 'moderate' },
]

const TRACES = [
  { id: 'trace_q9z4x2', channels: 'QR → Clipboard', status: 'active', events: 3 },
  { id: 'trace_m2k8p1', channels: 'Notification → Deep Link', status: 'active', events: 2 },
  { id: 'trace_x7n1w5', channels: 'Share → WebView', status: 'resolved', events: 4 },
]

export default function DashboardPreviewSection() {
  return (
    <LandingSection
      eyebrow="Control plane"
      title="Visibility across every boundary decision"
      lead="Monitor scans, decisions, risk pressure, and cross-channel traces from a single dashboard."
    >
      <div className="landing-dashboard">
        <div className="landing-dashboard__chrome">
          <span className="landing-dashboard__dot landing-dashboard__dot--red" />
          <span className="landing-dashboard__dot landing-dashboard__dot--yellow" />
          <span className="landing-dashboard__dot landing-dashboard__dot--green" />
          <span className="landing-dashboard__title">MAISB Dashboard</span>
          <span className="landing-dashboard__badge">Sample data</span>
        </div>

        <div className="landing-dashboard__grid">
          <article className="landing-dashboard__panel landing-dashboard__panel--wide">
            <header className="landing-dashboard__panel-head">
              <h3>Scans over time</h3>
              <span className="muted">Last 12 periods</span>
            </header>
            <div className="landing-dashboard__bars" aria-hidden="true">
              {SCAN_BARS.map((height, i) => (
                <span key={i} className="landing-dashboard__bar" style={{ height: `${height}%` }} />
              ))}
            </div>
            <p className="landing-dashboard__stat">
              <strong>2,847</strong>
              <span className="muted">total scans</span>
            </p>
          </article>

          <article className="landing-dashboard__panel">
            <header className="landing-dashboard__panel-head">
              <h3>Decision breakdown</h3>
            </header>
            <div className="landing-dashboard__donut" aria-hidden="true">
              <svg viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="4" />
                <circle cx="18" cy="18" r="14" fill="none" stroke="#22c55e" strokeWidth="4" strokeDasharray="52 36" strokeDashoffset="0" transform="rotate(-90 18 18)" />
                <circle cx="18" cy="18" r="14" fill="none" stroke="#fbbf24" strokeWidth="4" strokeDasharray="18 70" strokeDashoffset="-52" transform="rotate(-90 18 18)" />
                <circle cx="18" cy="18" r="14" fill="none" stroke="#ef4444" strokeWidth="4" strokeDasharray="18 70" strokeDashoffset="-70" transform="rotate(-90 18 18)" />
              </svg>
            </div>
            <ul className="landing-dashboard__legend">
              <li><span className="landing-dashboard__swatch landing-dashboard__swatch--allowed" />Allowed 78%</li>
              <li><span className="landing-dashboard__swatch landing-dashboard__swatch--review" />Review 14%</li>
              <li><span className="landing-dashboard__swatch landing-dashboard__swatch--blocked" />Blocked 8%</li>
            </ul>
          </article>

          <article className="landing-dashboard__panel">
            <header className="landing-dashboard__panel-head">
              <h3>Risk timeline</h3>
              <span className="muted">24h</span>
            </header>
            <div className="landing-dashboard__risk-line" aria-hidden="true">
              {RISK_DOTS.map((h, i) => (
                <span key={i} className="landing-dashboard__risk-dot" style={{ height: `${h}%` }} />
              ))}
            </div>
            <p className="landing-dashboard__stat">
              <strong>0.32</strong>
              <span className="muted">avg risk score</span>
            </p>
          </article>

          <article className="landing-dashboard__panel landing-dashboard__panel--wide">
            <header className="landing-dashboard__panel-head">
              <h3>Blocked payloads</h3>
              <span className="muted">Recent high-risk</span>
            </header>
            <div className="landing-dashboard__table-wrap">
              <table className="landing-dashboard__table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Channel</th>
                    <th>Risk</th>
                    <th>Trace</th>
                    <th>Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {BLOCKED_ROWS.map((row) => (
                    <tr key={row.trace}>
                      <td>{row.time}</td>
                      <td>{row.channel}</td>
                      <td>{row.score}</td>
                      <td><code>{row.trace}</code></td>
                      <td><span className="landing-dashboard__chip landing-dashboard__chip--blocked">BLOCKED</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="landing-dashboard__panel">
            <header className="landing-dashboard__panel-head">
              <h3>Channel reputation</h3>
            </header>
            <ul className="landing-dashboard__channels">
              {CHANNELS.map((ch) => (
                <li key={ch.name}>
                  <span>{ch.name}</span>
                  <div className="landing-dashboard__rep-bar">
                    <span className={`landing-dashboard__rep-fill landing-dashboard__rep-fill--${ch.status}`} style={{ width: `${ch.score}%` }} />
                  </div>
                  <span className="muted">{ch.score}</span>
                </li>
              ))}
            </ul>
          </article>

          <article className="landing-dashboard__panel">
            <header className="landing-dashboard__panel-head">
              <h3>Cross-channel traces</h3>
            </header>
            <ul className="landing-dashboard__traces">
              {TRACES.map((trace) => (
                <li key={trace.id}>
                  <div className="landing-dashboard__trace-head">
                    <code>{trace.id}</code>
                    <span className={`landing-dashboard__chip landing-dashboard__chip--${trace.status === 'active' ? 'active' : 'resolved'}`}>
                      {trace.status}
                    </span>
                  </div>
                  <p className="muted">{trace.channels} · {trace.events} events</p>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </div>
    </LandingSection>
  )
}
