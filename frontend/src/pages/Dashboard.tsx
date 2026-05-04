import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { Card } from '../components/Card'

export function DashboardPage() {
  const navigate = useNavigate()
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button variant="secondary" onClick={handleLogout}>Logout</Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <p className="text-gray-600">Total Boats</p>
            <p className="text-3xl font-bold">12</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-gray-600">Total Vehicles</p>
            <p className="text-3xl font-bold">28</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-gray-600">Active Expeditions</p>
            <p className="text-3xl font-bold">5</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-gray-600">Delivered</p>
            <p className="text-3xl font-bold">234</p>
          </div>
        </Card>
      </div>

      <div className="mt-8 space-y-4">
        <h2 className="text-xl font-bold">Quick Links</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="primary" className="w-full">➕ New Boat</Button>
          <Button variant="primary" className="w-full">➕ New Vehicle</Button>
          <Button variant="primary" className="w-full">➕ New Expedition</Button>
        </div>
      </div>
    </div>
  )
}
