import type { PropsWithChildren } from 'react'

export default function Badge({ children }: PropsWithChildren) {
  return <span className="badge">{children}</span>
}
