import type { PropsWithChildren, ReactNode } from 'react'
import Badge from './Badge'
import Card from './Card'

type Props = PropsWithChildren<{ title: string; subtitle?: string; sampleData?: boolean; actions?: ReactNode }>

export default function ChartCard({ title, subtitle, sampleData, actions, children }: Props) {
  return (
    <Card
      title={title}
      subtitle={subtitle}
      actions={
        <div className="row-inline">
          {sampleData && <Badge>Sample data</Badge>}
          {actions}
        </div>
      }
    >
      {children}
    </Card>
  )
}
