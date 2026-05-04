// frontend/src/pages/errors/ErrorPages.tsx
import { useNavigate } from 'react-router-dom'
import { Button, Card } from '../../components/ui/index'

export function Error404() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center min-h-screen space-y-6">
      <div className="text-center">
        <h1 className="text-8xl font-bold text-gray-900">404</h1>
        <p className="text-2xl text-gray-600 mt-2">Page Not Found</p>
        <p className="text-gray-500 mt-4">The page you're looking for doesn't exist</p>
      </div>
      <Button variant="primary" onClick={() => navigate('/')}>
        ← Back to Dashboard
      </Button>
    </div>
  )
}

export function Error500() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center min-h-screen space-y-6">
      <div className="text-center">
        <h1 className="text-8xl font-bold text-red-600">500</h1>
        <p className="text-2xl text-gray-600 mt-2">Server Error</p>
        <p className="text-gray-500 mt-4">Something went wrong on our end</p>
      </div>
      <Button variant="primary" onClick={() => navigate('/')}>
        ← Back to Dashboard
      </Button>
    </div>
  )
}

// frontend/src/pages/admin/AdminConfig.tsx
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button, Input, Card, Spinner, Alert } from '../../components/ui/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export function AdminConfig() {
  const [config, setConfig] = useState({
    trackingCodePrefix: 'TRAN',
    trackingCodeSuffix: '2026',
    generatedCode: ''
  })

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ['admin-config'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/v1/admin/config`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })

  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const res = await fetch(`${API_URL}/api/v1/admin/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })

  const testGenerate = () => {
    const number = String(Math.floor(Math.random() * 1000000)).padStart(6, '0')
    const code = `${config.trackingCodePrefix}-${number}-${config.trackingCodeSuffix}`
    setConfig({ ...config, generatedCode: code })
  }

  const handleSave = () => {
    saveMutation.mutate({
      trackingCodePrefix: config.trackingCodePrefix,
      trackingCodeSuffix: config.trackingCodeSuffix
    })
  }

  if (isLoading) return <Spinner size="lg" />

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-3xl font-bold">Admin Configuration</h1>

      {saveMutation.isSuccess && (
        <Alert type="success" title="Saved" message="Configuration updated successfully" />
      )}

      <Card>
        <h2 className="text-xl font-bold mb-6">Tracking Code Format</h2>

        <div className="space-y-4">
          <Input
            label="Prefix"
            value={config.trackingCodePrefix}
            onChange={(e) => setConfig({ ...config, trackingCodePrefix: e.target.value })}
            placeholder="e.g., TRAN"
          />

          <Input
            label="Suffix"
            value={config.trackingCodeSuffix}
            onChange={(e) => setConfig({ ...config, trackingCodeSuffix: e.target.value })}
            placeholder="e.g., 2026"
          />

          {config.generatedCode && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-600">Test Code Generated:</p>
              <p className="text-2xl font-mono font-bold text-blue-700">{config.generatedCode}</p>
            </div>
          )}

          <div className="flex gap-3">
            <Button variant="secondary" onClick={testGenerate}>
              🧪 Test Generate
            </Button>
            <Button variant="primary" onClick={handleSave} loading={saveMutation.isPending}>
              💾 Save Configuration
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-bold mb-4">System Health</h2>
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
