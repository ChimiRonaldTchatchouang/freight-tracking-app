import { Card } from '../components/Card'
import { Button } from '../components/Button'

export function BoatDetailPage() {
  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold">MS Neptune</h1>
        <div className="flex gap-2">
          <Button variant="primary">✏️ Edit</Button>
          <Button variant="danger">🗑️ Delete</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-bold mb-4">⛴️ Boat Info</h2>
          <div className="space-y-2">
            <p><span className="text-gray-600">Name:</span> MS Neptune</p>
            <p><span className="text-gray-600">IMO:</span> 1234567890</p>
            <p><span className="text-gray-600">Capacity:</span> 50000 kg</p>
            <p><span className="text-gray-600">Status:</span> Available</p>
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-bold mb-4">📍 Route Info</h2>
          <div className="space-y-2">
            <p><span className="text-gray-600">From:</span> Port of LA</p>
            <p><span className="text-gray-600">To:</span> Port of Rotterdam</p>
            <p><span className="text-gray-600">Created:</span> 2026-01-15</p>
            <p><span className="text-gray-600">Updated:</span> 2026-05-04</p>
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="text-xl font-bold mb-4">📊 Status History</h2>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <p>Available</p>
            <p className="text-sm text-gray-600">2026-05-04 10:30</p>
          </div>
          <div className="flex justify-between items-center">
            <p>In Transit</p>
            <p className="text-sm text-gray-600">2026-05-02 08:00</p>
          </div>
          <div className="flex justify-between items-center">
            <p>Created</p>
            <p className="text-sm text-gray-600">2026-01-15 14:00</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
