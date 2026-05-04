interface StatProps {
  label: string
  value: string | number
  icon: string
  color: 'blue' | 'green' | 'yellow' | 'red'
}

export function Stat({ label, value, icon, color }: StatProps) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600'
  }

  return (
    <div className={`p-6 rounded-lg ${colors[color]}`}>
      <p className="text-4xl mb-2">{icon}</p>
      <p className="text-gray-600 text-sm">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}
