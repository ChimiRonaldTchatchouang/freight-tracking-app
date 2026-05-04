import { useNavigate, useLocation } from 'react-router-dom'

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/boats', label: 'Boats', icon: '⛴️' },
    { path: '/vehicles', label: 'Vehicles', icon: '🚚' },
    { path: '/expeditions', label: 'Expeditions', icon: '📦' },
    { path: '/admin', label: 'Admin', icon: '⚙️' }
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white h-screen p-6 fixed left-0 top-0">
      <h2 className="text-2xl font-bold mb-8">🚢 Freight</h2>
      <nav className="space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`w-full text-left px-4 py-2 rounded-lg transition ${
              location.pathname === item.path
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <span className="mr-2">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <button
        onClick={() => {
          localStorage.removeItem('token')
          navigate('/login')
        }}
        className="absolute bottom-6 left-6 right-6 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
      >
        🚪 Logout
      </button>
    </aside>
  )
}
