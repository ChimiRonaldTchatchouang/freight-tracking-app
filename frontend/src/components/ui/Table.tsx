interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => React.ReactNode)
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  actions?: (row: T) => React.ReactNode
}

export function Table<T extends { id: string }>({ columns, data, actions }: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100 border-b">
            {columns.map((col, idx) => (
              <th key={idx} className="px-4 py-2 text-left font-semibold">
                {col.header}
              </th>
            ))}
            {actions && <th className="px-4 py-2 text-left font-semibold">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.id} className="border-b hover:bg-gray-50">
              {columns.map((col, idx) => (
                <td key={idx} className="px-4 py-2">
                  {typeof col.accessor === 'function' ? col.accessor(row) : (row[col.accessor] as React.ReactNode)}
                </td>
              ))}
              {actions && <td className="px-4 py-2 flex gap-2">{actions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
