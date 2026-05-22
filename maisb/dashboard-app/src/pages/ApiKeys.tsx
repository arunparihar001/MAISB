import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import DataTable from '../components/DataTable'
import EmptyState from '../components/EmptyState'
import { apiRequest } from '../lib/api'
import { getSelectedPlan, setApiKey, setApiKeyExists } from '../lib/auth'

type ApiKeyRow = {
  key_id: string
  key_prefix: string
  name: string
  scopes: string[]
  status: string
  created_at: string
  last_used_at?: string | null
}

type ApiKeysResponse = { api_keys: ApiKeyRow[] }
type ApiKeyCreateResponse = { key_id: string; api_key: string; key_prefix: string; name: string; scopes: string[]; status: string; created_at: string; warning?: string }
type UsageResponse = { usage: { total_scans: number } }

export default function ApiKeys() {
  const [keys, setKeys] = useState<ApiKeyRow[]>([])
  const [usage, setUsage] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('Default key')
  const [scopeInput, setScopeInput] = useState('scan')
  const [generatedRawKey, setGeneratedRawKey] = useState('')
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const isOnboarding = getSelectedPlan() === 'free' && keys.length === 0

  const scopes = useMemo(
    () => scopeInput.split(',').map((scope) => scope.trim()).filter(Boolean),
    [scopeInput],
  )

  async function loadKeys() {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<ApiKeysResponse>('/v1/api-keys')
      setKeys(data.api_keys || [])
      const hasKeys = (data.api_keys || []).some((key) => key.status !== 'revoked')
      setApiKeyExists(hasKeys)

      const usageItems = await Promise.all(
        (data.api_keys || []).map(async (key) => {
          try {
            const response = await apiRequest<UsageResponse>(`/v1/api-keys/${key.key_id}/usage`)
            return [key.key_id, response.usage.total_scans] as const
          } catch {
            return [key.key_id, 0] as const
          }
        }),
      )
      const nextUsage: Record<string, number> = {}
      usageItems.forEach(([keyId, total]) => {
        nextUsage[keyId] = total
      })
      setUsage(nextUsage)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadKeys().catch(() => undefined)
  }, [])

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const data = await apiRequest<ApiKeyCreateResponse>('/v1/api-keys', {
        method: 'POST',
        body: JSON.stringify({ name: newName, scopes: scopes.length ? scopes : ['scan'] }),
      })
      setGeneratedRawKey(data.api_key)
      setApiKey(data.api_key)
      setApiKeyExists(true)
      setShowCreate(false)
      await loadKeys()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function rotateKey(keyId: string) {
    setError('')
    try {
      const data = await apiRequest<{ new: { api_key: string } }>(`/v1/api-keys/${keyId}/rotate`, { method: 'POST' })
      setGeneratedRawKey(data.new.api_key)
      setApiKey(data.new.api_key)
      setApiKeyExists(true)
      await loadKeys()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function revokeKey(keyId: string) {
    setError('')
    try {
      await apiRequest<{ revoked: boolean }>(`/v1/api-keys/${keyId}/revoke`, { method: 'POST' })
      await loadKeys()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function copyRaw() {
    if (!generatedRawKey) return
    await navigator.clipboard.writeText(generatedRawKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <main className="stack">
      <div className="page-head">
        <h1>API Keys</h1>
        <div className="row-inline">
          <Button variant="secondary" onClick={() => setShowCreate(true)}>Generate API Key</Button>
          {isOnboarding && <Button onClick={() => navigate('/dashboard')}>Continue to Dashboard</Button>}
        </div>
      </div>

      {generatedRawKey && (
        <Card title="New API key generated" subtitle="This raw key is shown once. Save it now.">
          <p className="warning">Copy this key now. Do not expose production keys in GitHub, screenshots, or reports.</p>
          <code className="raw-key">{generatedRawKey}</code>
          <div className="row-inline" style={{ marginTop: '0.75rem' }}>
            <Button onClick={copyRaw}>{copied ? 'Copied' : 'Copy key'}</Button>
            <Button variant="secondary" onClick={() => setGeneratedRawKey('')}>Dismiss</Button>
          </div>
        </Card>
      )}

      {showCreate && (
        <Card title="Generate API Key" subtitle="Set display name and scopes.">
          <form className="form-grid" onSubmit={onCreate}>
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Key name" required />
            <input value={scopeInput} onChange={(e) => setScopeInput(e.target.value)} placeholder="Scopes (comma-separated)" />
            <div>
              <Badge>Scopes: {(scopes.length ? scopes : ['scan']).join(', ')}</Badge>
            </div>
            <div className="row-inline">
              <Button type="submit">Generate</Button>
              <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <Card><p>Loading API keys…</p></Card>
      ) : keys.length ? (
        <DataTable
          columns={[
            { key: 'prefix', label: 'Key Prefix', render: (row) => row.key_prefix },
            { key: 'created', label: 'Created', render: (row) => row.created_at || '—' },
            { key: 'used', label: 'Last Used', render: (row) => row.last_used_at || '—' },
            { key: 'usage', label: 'Usage', render: (row) => usage[row.key_id] ?? 0 },
            { key: 'scopes', label: 'Scopes', render: (row) => row.scopes.join(', ') || 'scan' },
            {
              key: 'status',
              label: 'Status',
              render: (row) => <Badge>{row.status}</Badge>,
            },
            {
              key: 'actions',
              label: 'Actions',
              render: (row) => (
                <div className="row-inline">
                  <Button variant="secondary" onClick={() => rotateKey(row.key_id)}>Rotate</Button>
                  <Button variant="danger" onClick={() => revokeKey(row.key_id)}>Revoke</Button>
                </div>
              ),
            },
          ]}
          rows={keys}
          rowKey={(row) => row.key_id}
        />
      ) : (
        <EmptyState title="No API keys yet" message="Generate your first API key to unlock protected dashboard routes." />
      )}

      {error && <p className="error">{error}</p>}
    </main>
  )
}
