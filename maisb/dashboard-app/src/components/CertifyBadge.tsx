type CertifyBadgeProps = {
  badgeUrl?: string
}

export default function CertifyBadge({ badgeUrl }: CertifyBadgeProps) {
  if (!badgeUrl) return null
  return (
    <section className="card">
      <h3>Certify Badge</h3>
      <img src={badgeUrl} alt="MAISB Certify badge" className="badge-image" />
    </section>
  )
}
