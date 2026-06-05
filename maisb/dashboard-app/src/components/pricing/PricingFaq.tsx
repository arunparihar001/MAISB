import { useState } from 'react'

const FAQS = [
  {
    id: 'scan',
    question: 'What is a scan?',
    answer:
      'A scan is a single POST /v1/scan request that evaluates mobile channel context — such as clipboard, QR, notification, or deep link content — and returns a runtime risk decision before it reaches your AI agent.',
  },
  {
    id: 'api-keys',
    question: 'How are API keys managed?',
    answer:
      'Generate, rotate, and revoke keys from your workspace dashboard. Raw keys are shown once at creation and never stored in plaintext again. Revoked keys stop working immediately.',
  },
  {
    id: 'payloads',
    question: 'Does MAISB store payloads?',
    answer:
      'No. MAISB uses a metadata-only architecture. Raw content is never persisted — only channel signals, risk scores, decisions, and audit metadata are retained.',
  },
  {
    id: 'self-hosted',
    question: 'Can MAISB be self-hosted?',
    answer:
      'Enterprise plans support on-prem and regional deployment options. Contact sales to discuss architecture, data residency, and SLA requirements for your organization.',
  },
]

export default function PricingFaq() {
  const [openId, setOpenId] = useState<string | null>(FAQS[0].id)

  return (
    <section className="pricing-faq">
      <header className="pricing-faq__head">
        <p className="eyebrow">FAQ</p>
        <h2>Common questions</h2>
      </header>
      <div className="pricing-faq__list">
        {FAQS.map((faq) => {
          const open = openId === faq.id
          return (
            <article key={faq.id} className={`pricing-faq__item${open ? ' pricing-faq__item--open' : ''}`}>
              <button
                type="button"
                className="pricing-faq__question"
                aria-expanded={open}
                onClick={() => setOpenId(open ? null : faq.id)}
              >
                <span>{faq.question}</span>
                <span className="pricing-faq__icon" aria-hidden="true">{open ? '−' : '+'}</span>
              </button>
              <div className="pricing-faq__collapse" aria-hidden={!open}>
                <div className="pricing-faq__collapse-inner">
                  <p className="pricing-faq__answer muted">{faq.answer}</p>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
