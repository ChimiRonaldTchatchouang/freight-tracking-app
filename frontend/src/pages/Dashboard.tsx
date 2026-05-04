import { useQuery } from '@tanstack/react-query'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export function Dashboard() {
  const { data: boats = [], isLoading } = useQuery({
    queryKey: ['boats'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats`)
      if (!res.ok) throw new Error('Failed to fetch boats')
      return res.json()
    }
  })

  const { data: vehicles = [] } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles`)
      if (!res.ok) throw new Error('Failed to fetch vehicles')
      return res.json()
    }
  })

  if (isLoading) return <div className="p-8">Loading...</div>

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-700">Total Boats</h2>
          <p className="text-4xl font-bold text-blue-600">{boats.length}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-700">Total Vehicles</h2>
          <p className="text-4xl font-bold text-green-600">{vehicles.length}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-4">Boats</h2>
        <div className="space-y-2">
          {boats.slice(0, 5).map((boat: any) => (
            <div key={boat.id} className="border-b pb-2">
              <p className="font-semibold">{boat.name}</p>
              <p className="text-sm text-gray-600">IMO: {boat.imoNumber} | Capacity: {boat.capacityKg}kg</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">Vehicles</h2>
        <div className="space-y-2">
          {vehicles.slice(0, 5).map((vehicle: any) => (
            <div key={vehicle.id} className="border-b pb-2">
              <p className="font-semibold">{vehicle.registrationPlate}</p>
              <p className="text-sm text-gray-600">Type: {vehicle.type} | Capacity: {vehicle.capacityKg}kg</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
