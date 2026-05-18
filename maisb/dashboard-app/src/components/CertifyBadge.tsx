export default function CertifyBadge({ badgeUrl }: { badgeUrl?: string }) {
  if (!badgeUrl) return null
  return (
    <div className="card">
      <h3>Badge Preview</h3>
      <img src={badgeUrl} alt="MAISB Certify badge" className="badge-image" />
    </div>
  )
}
