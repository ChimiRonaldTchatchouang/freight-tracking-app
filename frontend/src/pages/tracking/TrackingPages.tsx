// frontend/src/pages/tracking/PublicTracking.tsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button, Input, Card, Spinner, Breadcrumbs, StatusBadge, Alert } from '../../components/ui/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export function PublicTracking() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [trackingCode, setTrackingCode] = useState(code || '')

  const { data: expedition, isLoading, error } = useQuery({
    queryKey: ['tracking', trackingCode],
    queryFn: async () => {
      if (!trackingCode) return null
      const res = await fetch(`${API_URL}/api/v1/track/${trackingCode}`)
      if (!res.ok) throw new Error('Not found')
      return res.json()
    },
    enabled: !!trackingCode
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (trackingCode) {
      navigate(`/track/${trackingCode}`)
    }
  }

  const handleCopyCode = () => {
    navigator.clipboard.writeText(expedition?.trackingCode)
  }

  if (!trackingCode || isLoading) {
    return (
      <div className="space-y-8">
        <h1 className="text-4xl font-bold text-center">Track Your Shipment</h1>
        <p className="text-center text-gray-600 text-lg">Enter your tracking code to see the status of your maritime shipment</p>

        <Card className="max-w-md mx-auto">
          <form onSubmit={handleSearch} className="space-y-4">
            <Input
              placeholder="Enter tracking code (e.g., TRAN-000001-2026)"
              value={trackingCode}
              onChange={(e) => setTrackingCode(e.target.value)}
              required
            />
            <Button variant="primary" type="submit" className="w-full">
              Search
            </Button>
          </form>
        </Card>

        <p className="text-center text-gray-600">
          📱 <a href="/track/scan" className="text-blue-600 hover:underline">Scan QR Code</a>
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold">Track Your Shipment</h1>
        <Alert type="error" title="Not Found" message={`Tracking code "${trackingCode}" not found`} />
        <Button variant="secondary" onClick={() => navigate('/track')}>← Back to Search</Button>
      </div>
    )
  }

  if (!expedition) return <Spinner size="lg" />

  const statusSequence = [
    'creee', 'en_chargement', 'en_transit', 'en_attente_port', 
    'prete_enlèvement', 'livrée'
  ]
  const currentStatusIndex = statusSequence.indexOf(expedition.status)

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Your Shipment</h1>
          <p className="text-gray-600 mt-1">Tracking Code: <span className="font-mono font-bold">{expedition.trackingCode}</span></p>
        </div>
        <Button variant="secondary" onClick={handleCopyCode}>
          📋 Copy Code
        </Button>
      </div>

      {/* Status Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-blue-100">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 mb-2">Current Status</p>
            <StatusBadge status={expedition.status} />
          </div>
          <div className="text-right">
            <p className="text-gray-600 text-sm">Last Update</p>
            <p className="text-lg font-semibold">
              {new Date(expedition.updatedAt).toLocaleDateString()} {new Date(expedition.updatedAt).toLocaleTimeString()}
            </p>
          </div>
        </div>
      </Card>

      {/* Status Timeline */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Shipment Journey</h2>
        <div className="space-y-4">
          {statusSequence.map((status, idx) => (
            <div key={status} className="flex items-start gap-4">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                idx <= currentStatusIndex ? 'bg-green-600' : 'bg-gray-300'
              }`}>
                {idx <= currentStatusIndex ? '✓' : idx + 1}
              </div>
              <div className={`flex-1 pt-1 ${idx <= currentStatusIndex ? 'text-gray-900' : 'text-gray-400'}`}>
                <p className="font-semibold capitalize">{status.replace(/_/g, ' ')}</p>
                {idx === currentStatusIndex && (
                  <p className="text-sm text-green-600 mt-1">Currently at this stage</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Shipment Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-bold mb-4">📦 Cargo Information</h3>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-600">Description</p>
              <p className="font-semibold">{expedition.cargoDescription}</p>
            </div>
            <div>
              <p className="text-gray-600">Weight</p>
              <p className="font-semibold">{expedition.cargoWeightKg} kg</p>
            </div>
            <div>
              <p className="text-gray-600">Dimensions</p>
              <p className="font-semibold">
                {expedition.cargoLengthCm} × {expedition.cargoHeightCm} × {expedition.cargoWidthCm} cm
              </p>
            </div>
            {expedition.isFragile && (
              <div className="bg-yellow-50 p-2 rounded">
                <p className="text-yellow-800">🔨 Fragile Goods - Handle with care</p>
              </div>
            )}
            {expedition.requiresTemperature && (
              <div className="bg-blue-50 p-2 rounded">
                <p className="text-blue-800">❄️ Temperature Controlled: {expedition.temperatureCelsius}°C</p>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="font-bold mb-4">⛴️ Vessel Information</h3>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-600">Vessel</p>
              <p className="font-semibold">{expedition.boat?.name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-600">Capacity</p>
              <p className="font-semibold">{expedition.boat?.capacityKg || 'N/A'} kg</p>
            </div>
          </div>
        </Card>

        <Card className="md:col-span-2">
          <h3 className="font-bold mb-4">📍 Delivery Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600 font-semibold">From</p>
              <p>{expedition.shipperName}</p>
              <p className="text-gray-600">{expedition.shipperAddress}</p>
              <p className="text-gray-600">{expedition.shipperCity}, {expedition.shipperPostalCode}</p>
            </div>
            <div>
              <p className="text-gray-600 font-semibold">To</p>
              <p>{expedition.receiverName}</p>
              <p className="text-gray-600">{expedition.receiverAddress}</p>
              <p className="text-gray-600">{expedition.receiverCity}, {expedition.receiverPostalCode}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Actions */}
      <Card>
        <div className="flex gap-3 flex-wrap">
          <Button variant="primary">📥 Download PDF</Button>
          <Button variant="secondary">📧 Email Details</Button>
          <Button variant="secondary" onClick={() => window.print()}>🖨️ Print</Button>
          <Button variant="ghost" onClick={() => setTrackingCode('')}>🔍 Search Another</Button>
        </div>
      </Card>

      <p className="text-center text-gray-500 text-sm">
        Last updated: {new Date().toLocaleString()}
      </p>
    </div>
  )
}

// QR Scanner (Mobile)
export function QRScanner() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')

  const handleScan = (value: string) => {
    navigate(`/track/${value}`)
  }

  return (
    <div className="max-w-md mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Scan QR Code</h1>

      <Card className="text-center py-12">
        <p className="text-gray-600 mb-4">📱 Point your camera at the QR code</p>
        <p className="text-sm text-gray-500">QR Scanner integration coming soon</p>
      </Card>

      <Card>
        <p className="text-sm font-semibold mb-2">Or enter code manually:</p>
        <Input
          placeholder="TRAN-000001-2026"
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <Button variant="primary" className="w-full mt-3" onClick={() => handleScan(code)}>
          Search
        </Button>
      </Card>
    </div>
  )
}
