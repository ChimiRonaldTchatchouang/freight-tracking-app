import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'

export function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-xl text-gray-600">Page not found</p>
      <Button variant="primary" onClick={() => navigate('/dashboard')}>← Back to Dashboard</Button>
    </div>
  )
}
