import { clearAdminKey, clearApiKey } from '../lib/auth'

export default function Settings() {
  return <div className="stack"><h2>Settings</h2><div className="card"><p>Local MVP credentials are stored only in this browser.</p><button type="button" onClick={clearApiKey}>Clear API key</button><button type="button" className="secondary" onClick={clearAdminKey}>Clear admin key</button></div></div>
}
