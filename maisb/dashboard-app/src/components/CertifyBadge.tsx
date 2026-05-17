export default function CertifyBadge({ grade }: { grade: string }) {
  return <div className="card"><p>MAISB Certify</p><h3>Grade {grade || 'PENDING'}</h3></div>
}
