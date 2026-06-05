export default function FoundingBanner() {
  return (
    <section className="pricing-founding" aria-label="Founding customer offer">
      <div className="pricing-founding__inner">
        <div className="pricing-founding__head">
          <p className="pricing-founding__eyebrow">Founding Customers – Limited Time</p>
          <p className="pricing-founding__note muted">Promotional pricing for early adopters. Standard plan cards below reflect list pricing.</p>
        </div>
        <div className="pricing-founding__grid">
          <div className="pricing-founding__offer">
            <span className="pricing-founding__plan">Pro</span>
            <p className="pricing-founding__price">
              <span className="pricing-founding__strike">$99</span>
              <strong>$49</strong>
              <span className="muted">/month</span>
            </p>
          </div>
          <div className="pricing-founding__offer">
            <span className="pricing-founding__plan">Certify</span>
            <p className="pricing-founding__price">
              <span className="pricing-founding__strike">$499</span>
              <strong>$299</strong>
              <span className="muted">/month</span>
            </p>
          </div>
          <div className="pricing-founding__offer">
            <span className="pricing-founding__plan">Enterprise</span>
            <p className="pricing-founding__price pricing-founding__price--contact">
              <strong>Contact Sales</strong>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
