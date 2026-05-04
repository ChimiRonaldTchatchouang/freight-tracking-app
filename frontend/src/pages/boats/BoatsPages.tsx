// frontend/src/pages/boats/BoatsList.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Button, Input, Table, Pagination, Spinner, Card, StatusBadge } from '../../components/ui/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export function BoatsList() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const { data: boats = [], isLoading, error } = useQuery({
    queryKey: ['boats'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats`)
      if (!res.ok) throw new Error('Failed to fetch boats')
      return res.json()
    }
  })

  const filteredBoats = boats.filter((boat: any) =>
    boat.name.toLowerCase().includes(search.toLowerCase()) ||
    boat.imoNumber.includes(search)
  )

  const itemsPerPage = 10
  const totalPages = Math.ceil(filteredBoats.length / itemsPerPage)
  const paginatedBoats = filteredBoats.slice((page - 1) * itemsPerPage, page * itemsPerPage)

  if (isLoading) return <Spinner size="lg" />
  if (error) return <div className="text-red-600">Error loading boats</div>

  const columns = [
    { header: 'Name', accessor: (b: any) => b.name },
    { header: 'IMO', accessor: (b: any) => b.imoNumber },
    { header: 'Capacity', accessor: (b: any) => `${b.capacityKg} kg` },
    { header: 'Status', accessor: (b: any) => <StatusBadge status={b.status} /> }
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Boats</h1>
        <Button variant="primary" onClick={() => navigate('/boats/new')}>
          ➕ New Boat
        </Button>
      </div>

      <Card>
        <Input
          placeholder="Search by name or IMO..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      {paginatedBoats.length > 0 ? (
        <>
          <Card>
            <Table
              columns={columns}
              data={paginatedBoats}
              actions={(boat: any) => (
                <>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/boats/${boat.id}`)}
                  >
                    View
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/boats/${boat.id}/edit`)}
                  >
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
          <p className="text-gray-600">No boats found</p>
        </Card>
      )}
    </div>
  )
}

// frontend/src/pages/boats/BoatForm.tsx
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button, Input, Card, Spinner, Alert } from '../../components/ui/index'

export function BoatForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [formData, setFormData] = useState({
    name: '',
    imoNumber: '',
    capacityKg: '',
    portDeparture: '',
    portArrival: ''
  })
  const [error, setError] = useState('')

  // Fetch boat if editing
  const { data: boat } = useQuery({
    queryKey: ['boat', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats/${id}`)
      if (!res.ok) throw new Error('Failed to fetch boat')
      return res.json()
    },
    enabled: isEdit
  })

  useEffect(() => {
    if (boat) {
      setFormData(boat)
    }
  }, [boat])

  const mutation = useMutation({
    mutationFn: async (data) => {
      const url = isEdit ? `${API_URL}/api/v1/boats/${id}` : `${API_URL}/api/v1/boats`
      const method = isEdit ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!res.ok) throw new Error('Failed to save boat')
      return res.json()
    },
    onSuccess: () => {
      navigate('/boats')
    },
    onError: (err: any) => {
      setError(err.message)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{isEdit ? 'Edit Boat' : 'New Boat'}</h1>

      {error && <Alert type="error" title="Error" message={error} />}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />

          <Input
            label="IMO Number"
            value={formData.imoNumber}
            onChange={(e) => setFormData({ ...formData, imoNumber: e.target.value })}
            required
          />

          <Input
            label="Capacity (kg)"
            type="number"
            value={formData.capacityKg}
            onChange={(e) => setFormData({ ...formData, capacityKg: e.target.value })}
            required
          />

          <Input
            label="Port Departure"
            value={formData.portDeparture}
            onChange={(e) => setFormData({ ...formData, portDeparture: e.target.value })}
          />

          <Input
            label="Port Arrival"
            value={formData.portArrival}
            onChange={(e) => setFormData({ ...formData, portArrival: e.target.value })}
          />

          <div className="flex gap-3">
            <Button variant="primary" type="submit" loading={mutation.isPending}>
              Save
            </Button>
            <Button variant="secondary" onClick={() => navigate('/boats')}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

// frontend/src/pages/boats/BoatDetail.tsx
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button, Card, Spinner, StatusBadge, Breadcrumbs } from '../../components/ui/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export function BoatDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: boat, isLoading } = useQuery({
    queryKey: ['boat', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats/${id}`)
      if (!res.ok) throw new Error('Failed to fetch boat')
      return res.json()
    }
  })

  const deleteBoat = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/boats/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete boat')
      return res.json()
    },
    onSuccess: () => navigate('/boats')
  })

  if (isLoading) return <Spinner size="lg" />
  if (!boat) return <div>Boat not found</div>

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[
        { label: 'Boats', href: '/boats' },
        { label: boat.name }
      ]} />

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{boat.name}</h1>
        <StatusBadge status={boat.status} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">IMO Number</p>
              <p className="text-2xl font-bold">{boat.imoNumber}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Capacity</p>
              <p className="text-xl">{boat.capacityKg} kg</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Port Departure</p>
              <p className="text-lg">{boat.portDeparture || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Port Arrival</p>
              <p className="text-lg">{boat.portArrival || 'N/A'}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex gap-3">
          <Button variant="primary" onClick={() => navigate(`/boats/${id}/edit`)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => deleteBoat.mutate()}>
            Delete
          </Button>
          <Button variant="secondary" onClick={() => navigate('/boats')}>
            Back
          </Button>
        </div>
      </Card>
    </div>
  )
}
