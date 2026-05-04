interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const colors: Record<string, string> = {
    'Available': 'bg-green-100 text-green-800',
    'In Transit': 'bg-blue-100 text-blue-800',
    'Maintenance': 'bg-yellow-100 text-yellow-800',
    'Delivered': 'bg-green-500 text-white',
    'Created': 'bg-gray-100 text-gray-800'
  }
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  )
}
