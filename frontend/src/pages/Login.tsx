import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { Input } from '../components/Input'
import { Alert } from '../components/Alert'
import { Card } from '../components/Card'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiUrl, setApiUrl] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    // Get API URL
    const url = import.meta.env.VITE_API_URL
    setApiUrl(url || 'NOT SET')
    
    // Check if already logged in
    const token = localStorage.getItem('token')
    if (token) {
      navigate('/dashboard')
    }
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    // Validation
    if (!email || !password) {
      setError('Email and password required')
      setLoading(false)
      return
    }

    if (!apiUrl || apiUrl === 'NOT SET') {
      setError('⚠️ API URL not configured! Contact administrator.')
      setLoading(false)
      return
    }

    try {
      console.log('🔄 Attempting login...')
      console.log(`API URL: ${apiUrl}`)
      console.log(`Email: ${email}`)

      const url = `${apiUrl}/api/v1/auth/login`
      console.log(`POST ${url}`)

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      console.log(`Response status: ${res.status}`)
      console.log(`Response headers:`, res.headers)

      const data = await res.json()
      console.log('Response data:', data)

      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}: Login failed`)
      }

      if (!data.token) {
        throw new Error('No token received from server')
      }

      console.log('✅ Login successful!')
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user || {}))
      navigate('/dashboard')
    } catch (err: any) {
      console.error('❌ Login error:', err)
      setError(`Connection error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Main Login Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h1 className="text-3xl font-bold text-center mb-2">🚢 Freight Track</h1>
          <p className="text-gray-600 text-center mb-6">Maritime Logistics</p>
          
          {error && (
            <Alert 
              type="error" 
              message={error}
            />
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input 
              label="Email" 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="admin@freight-tracking.com"
              required 
            />
            <Input 
              label="Password" 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="Admin123!@#"
              required 
            />
            <Button 
              type="submit" 
              variant="primary" 
              loading={loading} 
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <hr className="my-6" />

          <div className="text-sm text-gray-600 space-y-2">
            <p><strong>Test Credentials:</strong></p>
            <p>Email: admin@freight-tracking.com</p>
            <p>Password: Admin123!@#</p>
          </div>
        </div>

        {/* Debug Info Card */}
        <Card className="mt-6">
          <h3 className="text-sm font-bold mb-2">🔧 Debug Info</h3>
          <div className="text-xs space-y-1 font-mono">
            <p className={`${apiUrl && apiUrl !== 'NOT SET' ? 'text-green-600' : 'text-red-600'}`}>
              API URL: {apiUrl ? '✓' : '✗'} {apiUrl}
            </p>
            <p>Frontend: {window.location.origin}</p>
            <p>
              <a 
                href="/debug" 
                className="text-blue-600 hover:underline"
              >
                → Go to Debug Page
              </a>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
