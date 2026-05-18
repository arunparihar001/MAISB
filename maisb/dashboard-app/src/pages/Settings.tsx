import { clearAdminKey, clearApiKey, getAdminKey, getApiKey, setAdminKey, setApiKey } from '../lib/auth'

export default function Settings() {
  return (
    <div className="stack">
      <h2>Settings</h2>
      <button type="button" onClick={() => setApiKey(getApiKey())}>Refresh API key storage</button>
      <button type="button" onClick={() => setAdminKey(getAdminKey())}>Refresh admin key storage</button>
      <button type="button" onClick={clearApiKey}>Clear API key</button>
      <button type="button" onClick={clearAdminKey}>Clear admin key</button>
    </div>
  )
}
