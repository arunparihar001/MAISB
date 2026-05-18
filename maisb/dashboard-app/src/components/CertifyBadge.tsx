type Props = { grade?: string; orderId?: string }

export default function CertifyBadge({ grade, orderId }: Props) {
  return <span className="badge">MAISB Certify {grade || (orderId ? 'Requested' : 'Pending')}</span>
}
