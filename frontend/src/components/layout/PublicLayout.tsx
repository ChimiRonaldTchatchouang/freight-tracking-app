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
