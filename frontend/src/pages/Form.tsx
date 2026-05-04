import { useState } from 'react'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Input } from '../components/Input'

interface FormPageProps {
  type: 'boat' | 'vehicle'
  mode: 'create' | 'edit'
}

export function FormPage({ type, mode }: FormPageProps) {
  const [formData, setFormData] = useState({
    name: mode === 'edit' ? 'MS Neptune' : '',
    imo: mode === 'edit' ? '1234567890' : '',
    capacity: mode === 'edit' ? '50000' : '',
    port: mode === 'edit' ? 'Port of LA' : ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission
    console.log('Form submitted:', formData)
  }

  const title = type === 'boat' 
    ? (mode === 'create' ? 'New Boat' : 'Edit Boat')
    : (mode === 'create' ? 'New Vehicle' : 'Edit Vehicle')

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{title}</h1>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          {type === 'boat' ? (
            <>
              <Input 
                label="Name" 
                value={formData.name} 
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required 
              />
              <Input 
                label="IMO Number" 
                value={formData.imo} 
                onChange={(e) => setFormData({...formData, imo: e.target.value})}
                required 
              />
              <Input 
                label="Capacity (kg)" 
                type="number"
                value={formData.capacity} 
                onChange={(e) => setFormData({...formData, capacity: e.target.value})}
                required 
              />
              <Input 
                label="Port" 
                value={formData.port} 
                onChange={(e) => setFormData({...formData, port: e.target.value})}
              />
            </>
          ) : (
            <>
              <Input 
                label="Registration Plate" 
                value={formData.name} 
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required 
              />
              <Input 
                label="Type" 
                value={formData.imo} 
                onChange={(e) => setFormData({...formData, imo: e.target.value})}
                required 
              />
              <Input 
                label="Capacity (kg)" 
                type="number"
                value={formData.capacity} 
                onChange={(e) => setFormData({...formData, capacity: e.target.value})}
                required 
              />
            </>
          )}

          <div className="flex gap-3 pt-4">
            <Button type="submit" variant="primary">Save</Button>
            <Button type="button" variant="secondary">Cancel</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
