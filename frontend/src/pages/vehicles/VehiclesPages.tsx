// frontend/src/pages/vehicles/VehiclesPages.tsx
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Input, Table, Pagination, Spinner, Card, StatusBadge, Breadcrumbs, Alert, Select } from '../../components/ui/index'
import { useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

// VEHICLES LIST
export function VehiclesList() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data: vehicles = [], isLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles`)
      if (!res.ok) throw new Error('Failed to fetch vehicles')
      return res.json()
    }
  })

  const filteredVehicles = vehicles.filter((v: any) =>
    v.registrationPlate.toLowerCase().includes(search.toLowerCase())
  )

  const itemsPerPage = 10
  const totalPages = Math.ceil(filteredVehicles.length / itemsPerPage)
  const paginatedVehicles = filteredVehicles.slice((page - 1) * itemsPerPage, page * itemsPerPage)

  if (isLoading) return <Spinner size="lg" />

  const columns = [
    { header: 'Plate', accessor: (v: any) => v.registrationPlate },
    { header: 'Type', accessor: (v: any) => v.type },
    { header: 'Capacity', accessor: (v: any) => `${v.capacityKg} kg` },
    { header: 'Status', accessor: (v: any) => <StatusBadge status={v.status} /> }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Vehicles</h1>
        <Button variant="primary" onClick={() => navigate('/vehicles/new')}>
          ➕ New Vehicle
        </Button>
      </div>

      <Card>
        <Input
          placeholder="Search by plate..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      {paginatedVehicles.length > 0 ? (
        <>
          <Card>
            <Table
              columns={columns}
              data={paginatedVehicles}
              actions={(vehicle: any) => (
                <>
                  <Button variant="secondary" size="sm" onClick={() => navigate(`/vehicles/${vehicle.id}`)}>
                    View
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => navigate(`/vehicles/${vehicle.id}/edit`)}>
                    Edit
                  </Button>
                </>
              )}
            />
          </Card>
          <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
        </>
      ) : (
        <Card className="text-center py-12">
          <p className="text-gray-600">No vehicles found</p>
        </Card>
      )}
    </div>
  )
}

// VEHICLE FORM
export function VehicleForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [formData, setFormData] = useState({
    registrationPlate: '',
    type: '',
    weightEmptyKg: '',
    capacityKg: ''
  })
  const [error, setError] = useState('')

  const { data: vehicle } = useQuery({
    queryKey: ['vehicle', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles/${id}`)
      if (!res.ok) throw new Error('Failed to fetch vehicle')
      return res.json()
    },
    enabled: isEdit
  })

  useEffect(() => {
    if (vehicle) setFormData(vehicle)
  }, [vehicle])

  const mutation = useMutation({
    mutationFn: async (data) => {
      const url = isEdit ? `${API_URL}/api/v1/vehicles/${id}` : `${API_URL}/api/v1/vehicles`
      const method = isEdit ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!res.ok) throw new Error('Failed to save vehicle')
      return res.json()
    },
    onSuccess: () => navigate('/vehicles'),
    onError: (err: any) => setError(err.message)
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{isEdit ? 'Edit Vehicle' : 'New Vehicle'}</h1>

      {error && <Alert type="error" title="Error" message={error} />}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Registration Plate"
            value={formData.registrationPlate}
            onChange={(e) => setFormData({ ...formData, registrationPlate: e.target.value })}
            required
          />

          <Select
            label="Type"
            options={[
              { value: 'camion', label: 'Truck' },
              { value: 'semi-remorque', label: 'Semi-truck' },
              { value: 'fourgonnette', label: 'Van' }
            ]}
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            required
          />

          <Input
            label="Empty Weight (kg)"
            type="number"
            value={formData.weightEmptyKg}
            onChange={(e) => setFormData({ ...formData, weightEmptyKg: e.target.value })}
            required
          />

          <Input
            label="Capacity (kg)"
            type="number"
            value={formData.capacityKg}
            onChange={(e) => setFormData({ ...formData, capacityKg: e.target.value })}
            required
          />

          <div className="flex gap-3">
            <Button variant="primary" type="submit" loading={mutation.isPending}>
              Save
            </Button>
            <Button variant="secondary" onClick={() => navigate('/vehicles')}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

// VEHICLE DETAIL
export function VehicleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: vehicle, isLoading } = useQuery({
    queryKey: ['vehicle', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles/${id}`)
      if (!res.ok) throw new Error('Failed to fetch vehicle')
      return res.json()
    }
  })

  const deleteVehicle = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/vehicles/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete vehicle')
      return res.json()
    },
    onSuccess: () => navigate('/vehicles')
  })

  if (isLoading) return <Spinner size="lg" />
  if (!vehicle) return <div>Vehicle not found</div>

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[
        { label: 'Vehicles', href: '/vehicles' },
        { label: vehicle.registrationPlate }
      ]} />

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{vehicle.registrationPlate}</h1>
        <StatusBadge status={vehicle.status} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Type</p>
              <p className="text-xl font-semibold">{vehicle.type}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Empty Weight</p>
              <p className="text-lg">{vehicle.weightEmptyKg} kg</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Capacity</p>
              <p className="text-xl font-semibold">{vehicle.capacityKg} kg</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Status</p>
              <p className="text-lg capitalize">{vehicle.status}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex gap-3">
          <Button variant="primary" onClick={() => navigate(`/vehicles/${id}/edit`)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => deleteVehicle.mutate()}>
            Delete
          </Button>
          <Button variant="secondary" onClick={() => navigate('/vehicles')}>
            Back
          </Button>
        </div>
      </Card>
    </div>
  )
}
