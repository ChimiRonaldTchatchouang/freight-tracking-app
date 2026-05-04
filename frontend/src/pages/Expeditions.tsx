import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Table } from '../components/Table'

export function ExpeditionsPage() {
  const expeditions = [
    { id: '1', code: 'TRAN-000001-2026', boat: 'MS Neptune', status: 'In Transit', created: '2026-05-01' },
    { id: '2', code: 'TRAN-000002-2026', boat: 'MS Atlantis', status: 'Delivered', created: '2026-04-30' },
    { id: '3', code: 'TRAN-000003-2026', boat: 'MS Neptune', status: 'Created', created: '2026-05-04' }
  ]

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Expeditions</h1>
        <Button variant="primary">➕ New Expedition</Button>
      </div>

      <Card>
        <Table columns={[
          { header: 'Tracking Code', accessor: 'code' as const },
          { header: 'Boat', accessor: 'boat' as const },
          { header: 'Status', accessor: 'status' as const },
          { header: 'Created', accessor: 'created' as const }
        ]} data={expeditions} />
      </Card>
    </div>
  )
}
