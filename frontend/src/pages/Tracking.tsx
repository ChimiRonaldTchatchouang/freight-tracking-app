import { useState } from 'react'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Input } from '../components/Input'

export function TrackingPage() {
  const [code, setCode] = useState('')
  const [found, setFound] = useState(false)

  const handleSearch = () => {
    if (code) {
      setFound(true)
    }
  }

  if (!found) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2">🚢 Track Shipment</h1>
            <p className="text-gray-600">Enter your tracking code to see status</p>
          </div>

          <Card>
            <div className="space-y-4">
              <Input 
                label="Tracking Code" 
                placeholder="TRAN-000001-2026" 
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
              <Button variant="primary" onClick={handleSearch} className="w-full">
                Search
              </Button>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <Button variant="secondary" onClick={() => setFound(false)}>← Back to Search</Button>
      </div>

      <h1 className="text-3xl font-bold mb-6">Shipment Status</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-bold mb-4">📦 Expedition Info</h2>
          <div className="space-y-2">
            <p><span className="text-gray-600">Code:</span> {code}</p>
            <p><span className="text-gray-600">Boat:</span> MS Neptune</p>
            <p><span className="text-gray-600">Status:</span> In Transit</p>
            <p><span className="text-gray-600">Updated:</span> 2026-05-04 10:30</p>
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-bold mb-4">📍 Route Info</h2>
          <div className="space-y-2">
            <p><span className="text-gray-600">From:</span> Port of LA</p>
            <p><span className="text-gray-600">To:</span> Port of Rotterdam</p>
            <p><span className="text-gray-600">Progress:</span> 60%</p>
            <p><span className="text-gray-600">ETA:</span> 2026-05-10</p>
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="text-xl font-bold mb-4">📊 Status Timeline</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-4">
            <span className="text-green-600 font-bold">✓</span>
            <div>
              <p className="font-semibold">Created</p>
              <p className="text-sm text-gray-600">2026-05-01 08:00</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <span className="text-green-600 font-bold">✓</span>
            <div>
              <p className="font-semibold">In Loading</p>
              <p className="text-sm text-gray-600">2026-05-02 14:30</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <span className="text-blue-600 font-bold">→</span>
            <div>
              <p className="font-semibold">In Transit</p>
              <p className="text-sm text-gray-600">2026-05-03 06:00 (Current)</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <span className="text-gray-400 font-bold">⭕</span>
            <div>
              <p className="font-semibold">Awaiting Port</p>
              <p className="text-sm text-gray-600">Expected: 2026-05-10</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <span className="text-gray-400 font-bold">⭕</span>
            <div>
              <p className="font-semibold">Delivered</p>
              <p className="text-sm text-gray-600">Expected: 2026-05-12</p>
            </div>
          </div>
        </div>
      </Card>

      <Card className="mt-6">
        <div className="flex gap-3">
          <Button variant="primary">📥 Download PDF</Button>
          <Button variant="secondary">📧 Email Status</Button>
          <Button variant="secondary">🖨️ Print</Button>
        </div>
      </Card>
    </div>
  )
}
