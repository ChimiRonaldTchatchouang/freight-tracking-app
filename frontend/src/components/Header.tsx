import { useNavigate } from 'react-router-dom'
import { Button } from './Button'

interface HeaderProps {
  title: string
}

export function Header({ title }: HeaderProps) {
  const navigate = useNavigate()

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">🚢 {title}</h1>
        <nav className="flex gap-4 items-center">
          <button onClick={() => navigate('/dashboard')} className="text-gray-600 hover:text-gray-900">Dashboard</button>
          <button onClick={() => navigate('/boats')} className="text-gray-600 hover:text-gray-900">Boats</button>
          <button onClick={() => navigate('/vehicles')} className="text-gray-600 hover:text-gray-900">Vehicles</button>
          <button onClick={() => navigate('/expeditions')} className="text-gray-600 hover:text-gray-900">Expeditions</button>
          <button onClick={() => navigate('/admin')} className="text-gray-600 hover:text-gray-900">Admin</button>
        </nav>
      </div>
    </header>
  )
}
