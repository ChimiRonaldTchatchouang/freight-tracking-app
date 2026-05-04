type Status = 'en_equipement' | 'pret_depart' | 'en_mer' | 'a_quai' | 'disponible' | 
             'creee' | 'en_chargement' | 'en_transit' | 'en_attente_port' | 'prete_enlèvement' | 'livrée' | 'annulée'

const statusColors: Record<Status, string> = {
  'en_equipement': 'bg-yellow-100 text-yellow-800',
  'pret_depart': 'bg-blue-100 text-blue-800',
  'en_mer': 'bg-cyan-100 text-cyan-800',
  'a_quai': 'bg-purple-100 text-purple-800',
  'disponible': 'bg-green-100 text-green-800',
  'creee': 'bg-gray-100 text-gray-800',
  'en_chargement': 'bg-orange-100 text-orange-800',
  'en_transit': 'bg-blue-100 text-blue-800',
  'en_attente_port': 'bg-yellow-100 text-yellow-800',
  'prete_enlèvement': 'bg-green-100 text-green-800',
  'livrée': 'bg-green-500 text-white',
  'annulée': 'bg-red-100 text-red-800'
}

interface BadgeProps {
  status: Status
  label?: string
}

export function StatusBadge({ status, label }: BadgeProps) {
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status]}`}>
      {label || status}
    </span>
  )
}
