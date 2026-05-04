// frontend/src/pages/auth/Login.tsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Input, Alert } from '../../components/ui/index'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      
      if (!response.ok) throw new Error('Login failed')
      
      const data = await response.json()
      localStorage.setItem('token', data.token)
      navigate('/dashboard')
    } catch (err) {
      setError('Email ou mot de passe incorrect')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900">🚢 Freight Track</h1>
            <p className="text-gray-600 mt-2">Maritime Logistics Management</p>
          </div>
          
          {error && <Alert type="error" title="Erreur" message={error} />}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
            >
              Sign In
            </Button>
          </form>
          
          <div className="mt-6 text-center text-sm">
            <a href="#" className="text-blue-600 hover:underline">Forgot password?</a>
          </div>
        </div>
      </div>
    </div>
  )
}

// frontend/src/components/layout/MainLayout.tsx
import React, { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'

export function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const navigate = useNavigate()
  
  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: '📊' },
    { label: 'Bateaux', path: '/boats', icon: '⛴️' },
    { label: 'Véhicules', path: '/vehicles', icon: '🚚' },
    { label: 'Expéditions', path: '/expeditions', icon: '📦' },
    { label: 'Admin', path: '/admin/config', icon: '⚙️' }
  ]
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-900 text-white transition-all duration-300 flex flex-col`}>
        <div className="p-4 border-b border-gray-800">
          <h1 className={`font-bold text-xl ${sidebarOpen ? '' : 'text-center'}`}>
            {sidebarOpen ? '🚢 FreightTrack' : '🚢'}
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition ${sidebarOpen ? '' : 'justify-center'}`}
            >
              <span className="text-xl">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>
        
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="w-full p-2 text-red-400 hover:bg-gray-800 rounded-lg transition"
          >
            {sidebarOpen ? 'Logout' : '🚪'}
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-600 hover:text-gray-900"
          >
            ☰
          </button>
          <h2 className="text-xl font-bold text-gray-900">Freight Tracking System</h2>
          <div className="w-10 h-10 bg-blue-600 rounded-full"></div>
        </header>
        
        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// frontend/src/components/layout/PublicLayout.tsx
import { Outlet } from 'react-router-dom'

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold">🚢 Freight Tracking</h1>
          <p className="text-gray-600">Track your maritime shipment</p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      
      <footer className="bg-gray-900 text-white mt-16 py-8 text-center">
        <p>© 2024 Freight Tracking. All rights reserved.</p>
      </footer>
    </div>
  )
}
