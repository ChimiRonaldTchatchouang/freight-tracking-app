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
      
      <div className="flex-1 flex flex-col overflow-hidden">
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
        
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
