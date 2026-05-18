type Props = {
  grade?: string
}

export default function CertifyBadge({ grade }: Props) {
  return <span className="badge">Certify {grade || 'Pending'}</span>
}
