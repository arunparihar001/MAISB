import type { ReactNode } from 'react'

type Props<T> = {
  columns: Array<{ key: string; label: string; render: (row: T) => ReactNode }>
  rows: T[]
  rowKey: (row: T, index: number) => string
}

export default function DataTable<T>({ columns, rows, rowKey }: Props<T>) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={rowKey(row, index)}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
