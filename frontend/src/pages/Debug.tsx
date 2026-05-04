import { useState, useEffect } from 'react'
import { Card } from '../components/Card'

export function DebugPage() {
  const [apiUrl, setApiUrl] = useState('')
  const [healthStatus, setHealthStatus] = useState<'checking' | 'ok' | 'error'>('checking')
  const [healthMessage, setHealthMessage] = useState('')
  const [loginTest, setLoginTest] = useState<'checking' | 'ok' | 'error'>('checking')
  const [loginMessage, setLoginMessage] = useState('')

  useEffect(() => {
    // Get API URL from env
    const url = import.meta.env.VITE_API_URL
    setApiUrl(url || 'NOT SET')

    // Test health endpoint
    if (url) {
      testHealth(url)
      testLogin(url)
    } else {
      setHealthStatus('error')
      setHealthMessage('VITE_API_URL not configured!')
      setLoginTest('error')
      setLoginMessage('VITE_API_URL not configured!')
    }
  }, [])

  const testHealth = async (url: string) => {
    try {
      const response = await fetch(`${url}/health`, {
        headers: { 'Content-Type': 'application/json' }
      })
      if (response.ok) {
        const data = await response.json()
        setHealthStatus('ok')
        setHealthMessage(`✓ Backend is healthy: ${JSON.stringify(data.status)}`)
      } else {
        setHealthStatus('error')
        setHealthMessage(`✗ Server returned ${response.status}`)
      }
    } catch (error: any) {
      setHealthStatus('error')
      setHealthMessage(`✗ Error: ${error.message}`)
    }
  }

  const testLogin = async (url: string) => {
    try {
      const response = await fetch(`${url}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@freight-tracking.com',
          password: 'Admin123!@#'
        })
      })

      const data = await response.json()

      if (response.ok && data.token) {
        setLoginTest('ok')
        setLoginMessage(`✓ Login successful! Token received.`)
      } else {
        setLoginTest('error')
        setLoginMessage(`✗ Login failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error: any) {
      setLoginTest('error')
      setLoginMessage(`✗ Error: ${error.message}`)
    }
  }

  const getStatusColor = (status: 'checking' | 'ok' | 'error') => {
    switch (status) {
      case 'ok':
        return 'bg-green-50 text-green-800 border-green-200'
      case 'error':
        return 'bg-red-50 text-red-800 border-red-200'
      default:
        return 'bg-yellow-50 text-yellow-800 border-yellow-200'
    }
  }

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">🔧 API Debug Page</h1>

      <Card className="mb-6">
        <h2 className="text-xl font-bold mb-4">Environment Variables</h2>
        <div className="space-y-2 bg-gray-50 p-4 rounded font-mono text-sm">
          <p>
            <span className="text-gray-600">VITE_API_URL:</span>{' '}
            <span className={apiUrl === 'NOT SET' ? 'text-red-600 font-bold' : 'text-green-600'}>
              {apiUrl}
            </span>
          </p>
          <p>
            <span className="text-gray-600">Frontend:</span>{' '}
            <span className="text-blue-600">{window.location.origin}</span>
          </p>
        </div>
      </Card>

      <Card className="mb-6">
        <h2 className="text-xl font-bold mb-4">Health Check</h2>
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Testing: {apiUrl}/health</p>
          <div className={`p-3 rounded border ${getStatusColor(healthStatus)}`}>
            {healthStatus === 'checking' ? '⏳ Checking...' : healthMessage}
          </div>
        </div>
      </Card>

      <Card className="mb-6">
        <h2 className="text-xl font-bold mb-4">Login Test</h2>
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Testing: {apiUrl}/api/v1/auth/login</p>
          <div className={`p-3 rounded border ${getStatusColor(loginTest)}`}>
            {loginTest === 'checking' ? '⏳ Checking...' : loginMessage}
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-bold mb-4">⚠️ Troubleshooting</h2>
        <div className="space-y-2 text-sm">
          {apiUrl === 'NOT SET' && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-red-800">
              <p className="font-bold">❌ VITE_API_URL NOT SET</p>
              <p>Configure VITE_API_URL in Vercel settings</p>
            </div>
          )}
          {healthStatus === 'error' && apiUrl !== 'NOT SET' && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-red-800">
              <p className="font-bold">❌ Backend Not Accessible</p>
              <p>Backend is not running or URL is wrong</p>
              <p className="text-xs mt-2">✓ Deploy backend on Railway</p>
              <p className="text-xs">✓ Get the Railway URL</p>
              <p className="text-xs">✓ Set VITE_API_URL in Vercel</p>
            </div>
          )}
          {loginTest === 'error' && healthStatus === 'ok' && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-red-800">
              <p className="font-bold">❌ Login Failed</p>
              <p>Check backend logs for details</p>
            </div>
          )}
          {loginTest === 'ok' && healthStatus === 'ok' && apiUrl !== 'NOT SET' && (
            <div className="p-3 rounded bg-green-50 border border-green-200 text-green-800">
              <p className="font-bold">✅ Everything Works!</p>
              <p>You can now close this debug page and login normally</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
