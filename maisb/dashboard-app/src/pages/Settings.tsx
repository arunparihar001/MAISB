import { clearApiKey, clearAdminKey } from '../lib/auth'

export default function Settings() {
  return (
    <main className="page">
      <h1>Settings</h1>
      <p>Clear local credentials for this browser session.</p>
      <button onClick={() => { clearApiKey(); clearAdminKey(); window.location.href = '/login' }}>Sign out</button>
    </main>
  )
}
