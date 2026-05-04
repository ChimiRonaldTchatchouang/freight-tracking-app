import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Table } from '../components/Table'

export function BoatsPage() {
  const boats = [
    { id: '1', name: 'MS Neptune', imo: '1234567890', capacity: '50000 kg', status: 'Available' },
    { id: '2', name: 'MS Atlantis', imo: '0987654321', capacity: '45000 kg', status: 'In Transit' }
  ]

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Boats</h1>
        <Button variant="primary">➕ New Boat</Button>
      </div>

      <Card>
        <Table columns={[
          { header: 'Name', accessor: 'name' as const },
          { header: 'IMO', accessor: 'imo' as const },
          { header: 'Capacity', accessor: 'capacity' as const },
          { header: 'Status', accessor: 'status' as const }
        ]} data={boats} />
      </Card>
    </div>
  )
}
