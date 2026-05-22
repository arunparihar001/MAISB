export const REQUIRED_CHANNELS = ['Clipboard', 'QR', 'Notification', 'Deep Link', 'Share Intent', 'WebView', 'NFC']

export const SAMPLE_SCANS_OVER_TIME = [
  { date: '2026-05-16', count: 42 },
  { date: '2026-05-17', count: 53 },
  { date: '2026-05-18', count: 37 },
  { date: '2026-05-19', count: 61 },
  { date: '2026-05-20', count: 58 },
  { date: '2026-05-21', count: 69 },
  { date: '2026-05-22', count: 64 },
]

export const SAMPLE_DECISION_BREAKDOWN = { BLOCKED: 28, REVIEW: 41, ALLOWED: 162 }

export const SAMPLE_RISK_DISTRIBUTION = {
  '0.0-0.24': 44,
  '0.25-0.49': 67,
  '0.50-0.74': 29,
  '0.75-1.00': 11,
}

export const SAMPLE_TOP_CHANNELS = REQUIRED_CHANNELS.map((channel, index) => ({
  channel,
  count: 20 + index * 6,
  avg_risk: 0.74 - index * 0.08,
}))

export function normalizeChannelName(channel: string): string {
  const value = channel.trim().toLowerCase()
  if (value === 'clipboard') return 'Clipboard'
  if (value === 'qr' || value === 'qr_code') return 'QR'
  if (value === 'notification' || value === 'push_notification') return 'Notification'
  if (value === 'deep_link') return 'Deep Link'
  if (value === 'share_intent') return 'Share Intent'
  if (value === 'webview') return 'WebView'
  if (value === 'nfc') return 'NFC'
  return channel
}
