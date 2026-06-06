export default function HeroVisual() {
  return (
    <div className="hero-visual" aria-hidden="true">
      <div className="hero-visual__grid" />
      <div className="hero-visual__glow" />

      <div className="hero-visual__pipeline">
        <div className="hero-visual__node hero-visual__node--channel">
          <span className="hero-visual__node-icon">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <rect x="5" y="2" width="10" height="16" rx="2" stroke="currentColor" strokeWidth="1.4" />
              <circle cx="10" cy="15.5" r="1" fill="currentColor" />
            </svg>
          </span>
          <span className="hero-visual__node-label">Mobile Channel</span>
          <span className="hero-visual__node-meta">clipboard · QR · NFC</span>
        </div>

        <div className="hero-visual__connector">
          <svg viewBox="0 0 48 12" fill="none" preserveAspectRatio="none">
            <line x1="0" y1="6" x2="48" y2="6" stroke="url(#flowGrad)" strokeWidth="1.5" strokeDasharray="4 3" className="hero-visual__flow-line" />
            <polygon points="44,3 48,6 44,9" fill="#60a5fa" />
            <defs>
              <linearGradient id="flowGrad" x1="0" y1="6" x2="48" y2="6" gradientUnits="userSpaceOnUse">
                <stop stopColor="#3b82f6" stopOpacity="0.3" />
                <stop offset="0.5" stopColor="#60a5fa" />
                <stop offset="1" stopColor="#34d399" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="hero-visual__node hero-visual__node--boundary">
          <span className="hero-visual__node-icon hero-visual__node-icon--shield">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M10 2l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V5l7-3z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="hero-visual__node-label">MAISB Boundary</span>
          <span className="hero-visual__node-meta">runtime scan</span>
        </div>

        <div className="hero-visual__connector">
          <svg viewBox="0 0 48 12" fill="none" preserveAspectRatio="none">
            <line x1="0" y1="6" x2="48" y2="6" stroke="url(#flowGrad2)" strokeWidth="1.5" strokeDasharray="4 3" className="hero-visual__flow-line hero-visual__flow-line--delay" />
            <polygon points="44,3 48,6 44,9" fill="#34d399" />
            <defs>
              <linearGradient id="flowGrad2" x1="0" y1="6" x2="48" y2="6" gradientUnits="userSpaceOnUse">
                <stop stopColor="#34d399" stopOpacity="0.3" />
                <stop offset="0.5" stopColor="#34d399" />
                <stop offset="1" stopColor="#fbbf24" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="hero-visual__node hero-visual__node--decision">
          <span className="hero-visual__node-icon hero-visual__node-icon--decision">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M4 10h12M10 4v12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.4" />
            </svg>
          </span>
          <span className="hero-visual__node-label">Risk Decision</span>
          <span className="hero-visual__node-meta">score · policy</span>
        </div>

        <div className="hero-visual__connector">
          <svg viewBox="0 0 48 12" fill="none" preserveAspectRatio="none">
            <line x1="0" y1="6" x2="48" y2="6" stroke="url(#flowGrad3)" strokeWidth="1.5" strokeDasharray="4 3" className="hero-visual__flow-line hero-visual__flow-line--delay2" />
            <polygon points="44,3 48,6 44,9" fill="#86efac" />
            <defs>
              <linearGradient id="flowGrad3" x1="0" y1="6" x2="48" y2="6" gradientUnits="userSpaceOnUse">
                <stop stopColor="#fbbf24" stopOpacity="0.3" />
                <stop offset="0.5" stopColor="#86efac" />
                <stop offset="1" stopColor="#86efac" stopOpacity="0.5" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="hero-visual__node hero-visual__node--llm">
          <span className="hero-visual__node-icon hero-visual__node-icon--llm">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <rect x="3" y="5" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.4" />
              <path d="M7 9h6M7 12h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
          </span>
          <span className="hero-visual__node-label">LLM Boundary</span>
          <span className="hero-visual__node-meta">agent context</span>
        </div>
      </div>

      <div className="hero-visual__panel">
        <div className="hero-visual__panel-head">
          <span className="hero-visual__method">POST</span>
          <code className="hero-visual__endpoint">/v1/scan</code>
          <span className="hero-visual__latency">24ms</span>
        </div>

        <div className="hero-visual__decisions">
          <span className="hero-visual__decision hero-visual__decision--blocked">BLOCKED</span>
          <span className="hero-visual__decision hero-visual__decision--review">REVIEW</span>
          <span className="hero-visual__decision hero-visual__decision--allowed">ALLOWED</span>
        </div>

        <div className="hero-visual__metrics">
          <div className="hero-visual__metric">
            <span className="hero-visual__metric-key">risk_score</span>
            <span className="hero-visual__metric-val hero-visual__metric-val--high">0.94</span>
          </div>
          <div className="hero-visual__metric">
            <span className="hero-visual__metric-key">cross_channel_trace</span>
            <span className="hero-visual__metric-val hero-visual__metric-val--active">
              <span className="hero-visual__pulse-dot" />
              active
            </span>
          </div>
          <div className="hero-visual__metric">
            <span className="hero-visual__metric-key">channel</span>
            <span className="hero-visual__metric-val">clipboard</span>
          </div>
        </div>

        <div className="hero-visual__risk-bar">
          <div className="hero-visual__risk-fill" />
        </div>
      </div>
    </div>
  )
}
