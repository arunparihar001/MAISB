import LandingSection from './LandingSection'
import {
  BellIcon,
  ClipboardIcon,
  LinkIcon,
  NfcIcon,
  QrIcon,
  ShareIcon,
  WebViewIcon,
} from './LandingIcons'

const CHANNELS = [
  {
    icon: ClipboardIcon,
    title: 'Clipboard',
    body: 'Detect paste-based prompt injection, instruction override, and exfiltration attempts before they reach your agent.',
  },
  {
    icon: QrIcon,
    title: 'QR codes',
    body: 'Scan QR payloads for embedded system prompts, malicious URLs, and encoded instruction chains at point of capture.',
  },
  {
    icon: BellIcon,
    title: 'Notifications',
    body: 'Inspect push notification content for hijacked prompts and social-engineering vectors forwarded to AI assistants.',
  },
  {
    icon: LinkIcon,
    title: 'Deep links',
    body: 'Sanitize URL parameters and intent payloads that carry prompt fragments into mobile AI workflows.',
  },
  {
    icon: NfcIcon,
    title: 'NFC',
    body: 'Evaluate NFC tag metadata and payload patterns that shift operational context in AI-integrated apps.',
  },
  {
    icon: ShareIcon,
    title: 'Share intents',
    body: 'Score content received through share sheets — a common vector for cross-app prompt injection.',
  },
  {
    icon: WebViewIcon,
    title: 'WebViews',
    body: 'Boundary-check DOM-derived context and embedded browser content before it is forwarded to the LLM.',
  },
]

export default function MobileChannelsSection() {
  return (
    <LandingSection
      eyebrow="Mobile channels"
      title="Every untrusted input surface, covered"
      lead="MAISB treats each mobile channel as an independent boundary — scored, traced, and enforced at runtime."
    >
      <div className="landing-channels">
        {CHANNELS.map(({ icon: Icon, title, body }) => (
          <article key={title} className="landing-channel">
            <span className="landing-channel__icon">
              <Icon />
            </span>
            <h3>{title}</h3>
            <p className="muted">{body}</p>
          </article>
        ))}
      </div>
    </LandingSection>
  )
}
