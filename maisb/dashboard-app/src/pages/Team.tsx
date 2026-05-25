import { FormEvent, useEffect, useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import DataTable from '../components/DataTable'
import { apiRequest } from '../lib/api'

type TeamMember = { member_id: string; email: string; name?: string; role: string; status: string }

type TeamResponse = { team: TeamMember[]; enterprise_actions?: { coming_soon?: boolean } }

type Invite = { invited: boolean; email: string; role: string; invite_id: string; status: string; message: string }

export default function Team() {
  const [team, setTeam] = useState<TeamMember[]>([])
  const [comingSoon, setComingSoon] = useState(false)
  const [tab, setTab] = useState<'members' | 'access' | 'activity'>('members')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('viewer')
  const [activity, setActivity] = useState<Array<{ id: string; entry: string }>>([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    apiRequest<TeamResponse>('/v1/team')
      .then((data) => {
        setTeam(data.team || [])
        setComingSoon(Boolean(data.enterprise_actions?.coming_soon))
      })
      .catch(() => {
        setTeam([])
        setComingSoon(true)
      })
  }, [])

  async function onInvite(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      const data = await apiRequest<Invite>('/v1/team/invite', {
        method: 'POST',
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      })
      setActivity((items) => [{ id: data.invite_id, entry: `Invited ${data.email} as ${data.role} (${data.status})` }, ...items])
      setMessage(data.message)
      setInviteEmail('')
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Enterprise permissions</p>
          <h1>Team</h1>
          <p className="muted">Invite members, review access, and audit activity.</p>
        </div>
        <Badge>{comingSoon ? 'Controls staged rollout' : 'Access online'}</Badge>
      </div>

      <Card
        title="Team console"
        actions={
          <div className="tab-strip">
            {(['members', 'access', 'activity'] as const).map((item) => (
              <button key={item} type="button" className={tab === item ? 'tab active' : 'tab'} onClick={() => setTab(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      >
        {tab === 'members' && (
          <div className="grid two-col">
            <form onSubmit={onInvite} className="form-grid card-inset">
              <h3>Invite member</h3>
              <input required type="email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="Member email" />
              <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                <option value="admin">admin</option>
                <option value="analyst">analyst</option>
                <option value="viewer">viewer</option>
              </select>
              <Button type="submit">Send invite</Button>
            </form>
            <div className="card-inset">
              <p className="eyebrow">Members</p>
              <DataTable
                columns={[
                  { key: 'name', label: 'Name', render: (row) => row.name || row.email },
                  { key: 'role', label: 'Role', render: (row) => <Badge>{row.role}</Badge> },
                  { key: 'status', label: 'Status', render: (row) => row.status },
                ]}
                rows={team}
                rowKey={(row) => row.member_id}
              />
            </div>
          </div>
        )}

        {tab === 'access' && (
          <Card title="Enterprise team controls">
            <p className="muted">Advanced role controls and provisioning workflows are coming soon for enterprise workspaces.</p>
            <ul className="bullet-list">
              <li>Least-privilege access reviews</li>
              <li>Provisioning and deprovisioning records</li>
              <li>Scoped workspace administration</li>
            </ul>
          </Card>
        )}

        {tab === 'activity' && (
          <Card title="Activity log">
            {activity.length ? (
              <ul className="bullet-list">
                {activity.map((item) => (
                  <li key={item.id}>{item.entry}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">No activity yet.</p>
            )}
          </Card>
        )}
      </Card>

      {message && <p className="notice">{message}</p>}
    </main>
  )
}
