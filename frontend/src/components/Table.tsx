interface TableProps<T> {
  columns: { header: string; accessor: keyof T }[]
  data: T[]
}

export function Table<T extends { id: string }>({ columns, data }: TableProps<T>) {
  return (
    <table className="w-full border-collapse">
      <thead>
        <tr className="bg-gray-100 border-b">
          {columns.map((col) => (
            <th key={String(col.accessor)} className="px-4 py-2 text-left">
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr key={row.id} className="border-b hover:bg-gray-50">
            {columns.map((col) => (
              <td key={String(col.accessor)} className="px-4 py-2">
                {String(row[col.accessor])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
