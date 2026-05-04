// frontend/src/pages/expeditions/ExpeditionsPages.tsx
import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Input, Table, Spinner, Card, StatusBadge, Breadcrumbs, Alert, Modal, Checkbox } from '../../components/ui/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

// EXPEDITIONS LIST
export function ExpeditionsList() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data: expeditions = [], isLoading } = useQuery({
    queryKey: ['expeditions'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/expeditions`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })

  const filtered = expeditions.filter((e: any) =>
    e.trackingCode.includes(search) || e.shipperName.toLowerCase().includes(search)
  )

  const itemsPerPage = 10
  const totalPages = Math.ceil(filtered.length / itemsPerPage)
  const paginated = filtered.slice((page - 1) * itemsPerPage, page * itemsPerPage)

  if (isLoading) return <Spinner size="lg" />

  const columns = [
    { header: 'Tracking Code', accessor: (e: any) => <span className="font-mono font-bold">{e.trackingCode}</span> },
    { header: 'Shipper', accessor: (e: any) => e.shipperName },
    { header: 'Status', accessor: (e: any) => <StatusBadge status={e.status} /> },
    { header: 'Created', accessor: (e: any) => new Date(e.createdAt).toLocaleDateString() }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Expeditions</h1>
        <Button variant="primary" onClick={() => navigate('/expeditions/new')}>
          ➕ New Expedition
        </Button>
      </div>

      <Card>
        <Input
          placeholder="Search by code or shipper..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      {paginated.length > 0 ? (
        <Card>
          <Table
            columns={columns}
            data={paginated}
            actions={(exp: any) => (
              <Button variant="secondary" size="sm" onClick={() => navigate(`/expeditions/${exp.id}`)}>
                View
              </Button>
            )}
          />
        </Card>
      ) : (
        <Card className="text-center py-12">
          <p className="text-gray-600">No expeditions found</p>
        </Card>
      )}
    </div>
  )
}

// EXPEDITIONS DETAIL
export function ExpeditionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: expedition, isLoading } = useQuery({
    queryKey: ['expedition', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/expeditions/${id}`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })

  if (isLoading) return <Spinner size="lg" />
  if (!expedition) return <div>Expedition not found</div>

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[
        { label: 'Expeditions', href: '/expeditions' },
        { label: expedition.trackingCode }
      ]} />

      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-mono">{expedition.trackingCode}</h1>
          <p className="text-gray-600 mt-2">Tracking Code (Copy: {expedition.trackingCode})</p>
        </div>
        <StatusBadge status={expedition.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-bold mb-4">Shipper Info</h3>
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-600">Name:</span> {expedition.shipperName}</p>
            <p><span className="text-gray-600">Email:</span> {expedition.shipperEmail}</p>
            <p><span className="text-gray-600">Phone:</span> {expedition.shipperPhone}</p>
            <p><span className="text-gray-600">Address:</span> {expedition.shipperAddress}</p>
          </div>
        </Card>

        <Card>
          <h3 className="font-bold mb-4">Receiver Info</h3>
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-600">Name:</span> {expedition.receiverName}</p>
            <p><span className="text-gray-600">Address:</span> {expedition.receiverAddress}</p>
            <p><span className="text-gray-600">City:</span> {expedition.receiverCity}</p>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="font-bold mb-4">Cargo Details</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600 text-sm">Description</p>
              <p className="font-semibold">{expedition.cargoDescription}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Weight</p>
              <p className="font-semibold">{expedition.cargoWeightKg} kg</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Dimensions</p>
              <p className="text-sm">{expedition.cargoLengthCm}×{expedition.cargoHeightCm}×{expedition.cargoWidthCm} cm</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Special Handling</p>
              <p className="text-sm">
                {expedition.isFragile && '🔨 Fragile'} {expedition.requiresTemperature && '❄️ Temperature controlled'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex gap-3">
          <Button variant="primary">Change Status</Button>
          <Button variant="secondary">Print PDF</Button>
          <Button variant="secondary" onClick={() => navigate('/expeditions')}>Back</Button>
        </div>
      </Card>
    </div>
  )
}

// EXPEDITIONS WIZARD (5 STEPS)
export function ExpeditionWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [boats, setBoats] = useState([])
  const [vehicles, setVehicles] = useState([])

  const [formData, setFormData] = useState({
    boatId: '',
    vehicleIds: [] as string[],
    shipperName: '',
    shipperEmail: '',
    shipperPhone: '',
    shipperAddress: '',
    shipperCity: '',
    shipperPostalCode: '',
    receiverName: '',
    receiverEmail: '',
    receiverAddress: '',
    receiverCity: '',
    receiverPostalCode: '',
    cargoDescription: '',
    cargoWeightKg: '',
    cargoLengthCm: '',
    cargoHeightCm: '',
    cargoWidthCm: '',
    isFragile: false,
    requiresTemperature: false,
    temperatureCelsius: '',
    specialInstructions: ''
  })

  useEffect(() => {
    fetch(`${API_URL}/api/v1/boats`).then(r => r.json()).then(setBoats)
    fetch(`${API_URL}/api/v1/vehicles`).then(r => r.json()).then(setVehicles)
  }, [])

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/expeditions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    onSuccess: (data) => {
      navigate(`/expeditions/${data.id}`)
    }
  })

  const nextStep = () => step < 5 && setStep(step + 1)
  const prevStep = () => step > 1 && setStep(step - 1)

  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">New Expedition</h1>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {[1, 2, 3, 4, 5].map((s) => (
            <div
              key={s}
              className={`w-full h-2 rounded-full ${s <= step ? 'bg-blue-600' : 'bg-gray-300'} ${s < 5 ? 'mr-2' : ''}`}
            />
          ))}
        </div>
        <p className="text-center text-sm text-gray-600">Step {step} of 5</p>
      </div>

      <Card>
        {/* STEP 1: Select Boat */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Select Boat</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {boats.map((boat: any) => (
                <button
                  key={boat.id}
                  onClick={() => setFormData({ ...formData, boatId: boat.id })}
                  className={`p-3 border rounded-lg text-left ${
                    formData.boatId === boat.id ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
                  }`}
                >
                  <p className="font-semibold">{boat.name}</p>
                  <p className="text-sm text-gray-600">{boat.capacityKg} kg capacity</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* STEP 2: Select Vehicles */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Select Vehicles</h2>
            <div className="space-y-2">
              {vehicles.map((vehicle: any) => (
                <Checkbox
                  key={vehicle.id}
                  label={`${vehicle.registrationPlate} (${vehicle.capacityKg} kg)`}
                  checked={formData.vehicleIds.includes(vehicle.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData({ ...formData, vehicleIds: [...formData.vehicleIds, vehicle.id] })
                    } else {
                      setFormData({ ...formData, vehicleIds: formData.vehicleIds.filter(id => id !== vehicle.id) })
                    }
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* STEP 3: Shipper Info */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Shipper Information</h2>
            <Input label="Name" value={formData.shipperName} onChange={(e) => setFormData({ ...formData, shipperName: e.target.value })} />
            <Input label="Email" type="email" value={formData.shipperEmail} onChange={(e) => setFormData({ ...formData, shipperEmail: e.target.value })} />
            <Input label="Phone" value={formData.shipperPhone} onChange={(e) => setFormData({ ...formData, shipperPhone: e.target.value })} />
            <Input label="Address" value={formData.shipperAddress} onChange={(e) => setFormData({ ...formData, shipperAddress: e.target.value })} />
            <Input label="City" value={formData.shipperCity} onChange={(e) => setFormData({ ...formData, shipperCity: e.target.value })} />
          </div>
        )}

        {/* STEP 4: Receiver Info */}
        {step === 4 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Receiver Information</h2>
            <Input label="Name" value={formData.receiverName} onChange={(e) => setFormData({ ...formData, receiverName: e.target.value })} />
            <Input label="Address" value={formData.receiverAddress} onChange={(e) => setFormData({ ...formData, receiverAddress: e.target.value })} />
            <Input label="City" value={formData.receiverCity} onChange={(e) => setFormData({ ...formData, receiverCity: e.target.value })} />
          </div>
        )}

        {/* STEP 5: Cargo Details */}
        {step === 5 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Cargo Details</h2>
            <Input label="Description" value={formData.cargoDescription} onChange={(e) => setFormData({ ...formData, cargoDescription: e.target.value })} />
            <Input label="Weight (kg)" type="number" value={formData.cargoWeightKg} onChange={(e) => setFormData({ ...formData, cargoWeightKg: e.target.value })} />
            <div className="grid grid-cols-3 gap-2">
              <Input label="Length (cm)" type="number" value={formData.cargoLengthCm} onChange={(e) => setFormData({ ...formData, cargoLengthCm: e.target.value })} />
              <Input label="Height (cm)" type="number" value={formData.cargoHeightCm} onChange={(e) => setFormData({ ...formData, cargoHeightCm: e.target.value })} />
              <Input label="Width (cm)" type="number" value={formData.cargoWidthCm} onChange={(e) => setFormData({ ...formData, cargoWidthCm: e.target.value })} />
            </div>
            <Checkbox label="Fragile?" checked={formData.isFragile} onChange={(e) => setFormData({ ...formData, isFragile: e.target.checked })} />
            <Checkbox label="Temperature Controlled?" checked={formData.requiresTemperature} onChange={(e) => setFormData({ ...formData, requiresTemperature: e.target.checked })} />
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex gap-3 mt-6 pt-6 border-t">
          <Button variant="secondary" onClick={prevStep} disabled={step === 1}>← Previous</Button>
          <Button variant="primary" onClick={nextStep} disabled={step === 5} loading={false}>Next →</Button>
          {step === 5 && (
            <Button variant="primary" onClick={() => createMutation.mutate()} loading={createMutation.isPending}>Create Expedition</Button>
          )}
          <Button variant="ghost" onClick={() => navigate('/expeditions')}>Cancel</Button>
        </div>
      </Card>
    </div>
  )
}
