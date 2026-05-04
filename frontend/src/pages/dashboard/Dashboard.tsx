// frontend/src/pages/dashboard/Dashboard.tsx
import { useQuery } from '@tanstack/react-query'
import { Card, Spinner } from '../../components/ui/index'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

interface KPICardProps {
  title: string
  value: number | string
  icon: string
  color: string
}

function KPICard({ title, value, icon, color }: KPICardProps) {
  return (
    <Card className={`bg-gradient-to-br from-${color}-50 to-${color}-100`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="text-5xl">{icon}</div>
      </div>
    </Card>
  )
}

export function Dashboard() {
  // Fetch boats
  const { data: boats = [], isLoading: boatsLoading } = useQuery({
    queryKey: ['boats'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats`)
      if (!res.ok) throw new Error('Failed to fetch boats')
      return res.json()
    }
  })

  // Fetch vehicles
  const { data: vehicles = [], isLoading: vehiclesLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles`)
      if (!res.ok) throw new Error('Failed to fetch vehicles')
      return res.json()
    }
  })

  // Fetch expeditions (dummy data for now)
  const expeditionsActive = 5
  const expeditionsDelivered = 23

  if (boatsLoading || vehiclesLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  // Prepare chart data
  const boatsByStatus = [
    { name: 'Available', value: boats.filter((b: any) => b.status === 'disponible').length },
    { name: 'In Transit', value: boats.filter((b: any) => b.status === 'en_mer').length },
    { name: 'At Port', value: boats.filter((b: any) => b.status === 'a_quai').length },
    { name: 'Maintenance', value: boats.filter((b: any) => b.status === 'en_equipement').length }
  ]

  const vehiclesByType = [
    { name: 'Truck', value: vehicles.filter((v: any) => v.type === 'camion').length },
    { name: 'Semi-truck', value: vehicles.filter((v: any) => v.type === 'semi-remorque').length },
    { name: 'Van', value: vehicles.filter((v: any) => v.type === 'fourgonnette').length }
  ]

  const expeditionsChart = [
    { date: 'Mon', count: 3 },
    { date: 'Tue', count: 5 },
    { date: 'Wed', count: 4 },
    { date: 'Thu', count: 7 },
    { date: 'Fri', count: 6 },
    { date: 'Sat', count: 2 },
    { date: 'Sun', count: 1 }
  ]

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back! Here's your fleet overview.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Boats" value={boats.length} icon="⛴️" color="blue" />
        <KPICard title="Total Vehicles" value={vehicles.length} icon="🚚" color="green" />
        <KPICard title="Active Expeditions" value={expeditionsActive} icon="📦" color="yellow" />
        <KPICard title="Delivered" value={expeditionsDelivered} icon="✅" color="purple" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Boats by Status */}
        <Card>
          <h3 className="text-lg font-bold mb-4">Boats by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={boatsByStatus}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {boatsByStatus.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Vehicles by Type */}
        <Card>
          <h3 className="text-lg font-bold mb-4">Vehicles by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={vehiclesByType}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Expeditions per Day */}
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-bold mb-4">Expeditions per Day (Last 7 days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={expeditionsChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <h3 className="text-lg font-bold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg text-blue-700 font-semibold transition">
            ➕ New Boat
          </button>
          <button className="p-4 bg-green-50 hover:bg-green-100 rounded-lg text-green-700 font-semibold transition">
            ➕ New Vehicle
          </button>
          <button className="p-4 bg-yellow-50 hover:bg-yellow-100 rounded-lg text-yellow-700 font-semibold transition">
            ➕ New Expedition
          </button>
        </div>
      </Card>
    </div>
  )
}
