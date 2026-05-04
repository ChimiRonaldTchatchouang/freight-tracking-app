import { useState } from 'react'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { Input } from '../components/Input'

export function AdminPage() {
  const [prefix, setPrefix] = useState('TRAN')
  const [suffix, setSuffix] = useState('2026')

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">Admin Configuration</h1>

      <Card className="mb-6">
        <h2 className="text-xl font-bold mb-4">⚙️ Tracking Code Format</h2>
        <div className="space-y-4">
          <Input label="Prefix" value={prefix} onChange={(e) => setPrefix(e.target.value)} />
          <Input label="Suffix" value={suffix} onChange={(e) => setSuffix(e.target.value)} />
          
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-600">Preview:</p>
            <p className="text-2xl font-mono font-bold text-blue-700">
              {prefix}-000001-{suffix}
            </p>
          </div>

          <div className="flex gap-3">
            <Button variant="primary">💾 Save Config</Button>
            <Button variant="secondary">🧪 Test Generate</Button>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-bold mb-4">🏥 System Health</h2>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <p>Database Connection</p>
            <span className="text-green-600 font-semibold">✓ Connected</span>
          </div>
          <div className="flex justify-between items-center">
            <p>API Health</p>
            <span className="text-green-600 font-semibold">✓ Healthy</span>
          </div>
          <div className="flex justify-between items-center">
            <p>Email Service</p>
            <span className="text-yellow-600 font-semibold">⚠ Configured</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
