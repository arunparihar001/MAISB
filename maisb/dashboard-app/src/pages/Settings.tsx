import { setApiKey } from '../lib/auth'

export default function Settings() {
  return <main className="page"><h1>Settings</h1><button onClick={() => { setApiKey(''); window.location.href = '/login' }}>Sign out</button></main>
}
