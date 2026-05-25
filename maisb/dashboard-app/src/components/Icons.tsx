type IconProps = { className?: string }

function baseClass(className = '') {
  return `icon ${className}`.trim()
}

export function ShieldIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 5 6v5c0 5 3.4 8.7 7 10 3.6-1.3 7-5 7-10V6l-7-3Z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round" />
      <path d="M12 7.5v8" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <path d="M9.5 11h5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  )
}

export function GridIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="4" y="4" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.75" />
      <rect x="14" y="4" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.75" />
      <rect x="4" y="14" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.75" />
      <rect x="14" y="14" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.75" />
    </svg>
  )
}

export function RadarIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.75" />
      <path d="M12 4v8l5 3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 20a8 8 0 1 0-8-8" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  )
}

export function TraceIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 7h4a3 3 0 0 1 3 3v4a3 3 0 0 0 3 3h4" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <path d="M5 17h4a3 3 0 0 0 3-3V8a3 3 0 0 1 3-3h4" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <circle cx="5" cy="7" r="1.5" fill="currentColor" />
      <circle cx="19" cy="17" r="1.5" fill="currentColor" />
    </svg>
  )
}

export function KeyIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="9" cy="11" r="4" stroke="currentColor" strokeWidth="1.75" />
      <path d="M13 11h8l-2 2 2 2h-2l-1 1-2-2h-1" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function UsersIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M16 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-1A3.5 3.5 0 0 0 8 17.5V19" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <circle cx="12" cy="8" r="3" stroke="currentColor" strokeWidth="1.75" />
      <path d="M19 19v-1a3 3 0 0 0-3-3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <path d="M17 5.8a2.4 2.4 0 0 1 0 4.4" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  )
}

export function SettingsIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75" />
      <path d="M19.4 15a1.9 1.9 0 0 0 .4 2.1l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.9 1.9 0 0 0-2.1-.4 1.9 1.9 0 0 0-1.1 1.7V21a2 2 0 1 1-4 0v-.2a1.9 1.9 0 0 0-1.1-1.7 1.9 1.9 0 0 0-2.1.4l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.9 1.9 0 0 0 .4-2.1 1.9 1.9 0 0 0-1.7-1.1H3a2 2 0 1 1 0-4h.2a1.9 1.9 0 0 0 1.7-1.1 1.9 1.9 0 0 0-.4-2.1l-.1-.1A2 2 0 1 1 7.2 3l.1.1a1.9 1.9 0 0 0 2.1.4A1.9 1.9 0 0 0 10.5 1.8V2a2 2 0 1 1 4 0v-.2a1.9 1.9 0 0 0 1.1 1.7 1.9 1.9 0 0 0 2.1-.4l.1-.1A2 2 0 1 1 20.6 6l-.1.1a1.9 1.9 0 0 0-.4 2.1 1.9 1.9 0 0 0 1.7 1.1H22a2 2 0 1 1 0 4h-.2a1.9 1.9 0 0 0-1.7 1.1Z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
    </svg>
  )
}

export function SparkIcon({ className = '' }: IconProps) {
  return (
    <svg className={baseClass(className)} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round" />
      <path d="m18 14 1 2.8L22 18l-3 .9L18 22l-.9-3.1L14 18l3.1-1.2L18 14Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  )
}
