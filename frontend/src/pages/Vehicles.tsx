import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Table } from '../components/Table'

export function VehiclesPage() {
  const vehicles = [
    { id: '1', plate: 'ABC-1234', type: 'Truck', capacity: '20000 kg', status: 'Available' },
    { id: '2', plate: 'XYZ-5678', type: 'Semi-truck', capacity: '30000 kg', status: 'In Transit' },
    { id: '3', plate: 'DEF-9999', type: 'Van', capacity: '5000 kg', status: 'Maintenance' }
  ]

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Vehicles</h1>
        <Button variant="primary">➕ New Vehicle</Button>
      </div>

      <Card>
        <Table columns={[
          { header: 'Plate', accessor: 'plate' as const },
          { header: 'Type', accessor: 'type' as const },
          { header: 'Capacity', accessor: 'capacity' as const },
          { header: 'Status', accessor: 'status' as const }
        ]} data={vehicles} />
      </Card>
    </div>
  )
}
