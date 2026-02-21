import { useState, useEffect } from 'react'

const API = '/api'

function formatTimestamp(ts) {
  if (!ts) return '—'
  return ts.slice(0, 19).replace('T', ' ')
}

function MetricCard({ label, value, color }) {
  const pct = ((value ?? 0) * 100).toFixed(1)
  return (
    <div className="metric-card" style={{ borderColor: color }}>
      <div className="metric-value" style={{ color }}>{pct}%</div>
      <div className="metric-label">{label}</div>
    </div>
  )
}

function ReportDetail({ report }) {
  if (!report) return null
  const { metrics = {}, channel_breakdown = {}, timestamp, model_id, pack_version } = report
  return (
    <div>
      <div className="report-meta">
        <span>Pack: <b>{pack_version}</b></span>
        <span>Model: <b>{model_id}</b></span>
        <span>Time: <b>{formatTimestamp(timestamp)}</b></span>
      </div>

      <div className="metrics-row">
        <MetricCard label="Attack Detection Rate" value={metrics.attack_detection_rate} color="#2ecc71" />
        <MetricCard label="False Positive Rate"   value={metrics.false_positive_rate}   color="#e74c3c" />
        <MetricCard label="Accuracy"              value={metrics.accuracy}              color="#3498db" />
      </div>

      <div className="counts-row">
        <span>Total: <b>{metrics.total ?? 0}</b></span>
        <span>Attacks: <b>{metrics.attack_count ?? 0}</b></span>
        <span>Benign: <b>{metrics.benign_count ?? 0}</b></span>
        <span>TP: <b>{metrics.true_positives ?? 0}</b></span>
        <span>FP: <b>{metrics.false_positives ?? 0}</b></span>
        <span>FN: <b>{metrics.false_negatives ?? 0}</b></span>
      </div>

      {Object.keys(channel_breakdown).length > 0 && (
        <div>
          <h3>Channel Breakdown</h3>
          <table className="channel-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Total</th>
                <th>Detection Rate</th>
                <th>FP Rate</th>
                <th>Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(channel_breakdown).map(([ch, m]) => (
                <tr key={ch}>
                  <td>{ch}</td>
                  <td>{m.total}</td>
                  <td>{((m.attack_detection_rate ?? 0) * 100).toFixed(1)}%</td>
                  <td>{((m.false_positive_rate ?? 0) * 100).toFixed(1)}%</td>
                  <td>{((m.accuracy ?? 0) * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [reports, setReports] = useState([])
  const [selected, setSelected] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/reports`)
      .then((r) => r.json())
      .then((d) => setReports(d.reports ?? []))
      .catch(() => setError('Could not connect to the backend API. Is it running on port 8000?'))
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setError(null)
    fetch(`${API}/reports/${selected}`)
      .then((r) => r.json())
      .then((d) => { setReport(d); setLoading(false) })
      .catch(() => { setError('Failed to load report'); setLoading(false) })
  }, [selected])

  return (
    <div className="app">
      <header className="app-header">
        <h1>MAISB Dashboard</h1>
        <span className="version">v0.3.0</span>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <h2>Reports</h2>
          {error && <div className="error">{error}</div>}
          {reports.length === 0 && !error && (
            <p className="empty">No reports found.<br />Run an evaluation first:<br /><code>maisb quick</code></p>
          )}
          <ul className="report-list">
            {reports.map((name) => (
              <li
                key={name}
                className={name === selected ? 'active' : ''}
                onClick={() => { setSelected(name); setReport(null) }}
              >
                {name}
              </li>
            ))}
          </ul>
        </aside>

        <main className="main-content">
          {loading && <p className="placeholder">Loading…</p>}
          {!loading && !selected && (
            <p className="placeholder">Select a report from the sidebar to view its metrics.</p>
          )}
          {!loading && report && Array.isArray(report) && (
            <p className="placeholder">
              This is a sweep report ({report.length} runs).
              Individual run reports appear in the sidebar.
            </p>
          )}
          {!loading && report && !Array.isArray(report) && (
            <ReportDetail report={report} />
          )}
        </main>
      </div>
    </div>
  )
}
