import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import { getApiKey } from '../lib/auth'
import UsageChart from '../components/UsageChart'

export default function Usage() {
  const [used, setUsed] = useState(0)
  const [limit, setLimit] = useState(1000)
  useEffect(() => {
    const apiKey = getApiKey()
    if (!apiKey) return
    apiGet<{ scan_count: number; limit: number }>('/v1/public/usage', { api_key: apiKey }).then((d) => {
      setUsed(d.scan_count || 0)
      setLimit(d.limit || 0)
    }).catch(() => undefined)
  }, [])
  return <main className="page"><h1>Usage + quota</h1><UsageChart used={used} limit={limit} /></main>
}
