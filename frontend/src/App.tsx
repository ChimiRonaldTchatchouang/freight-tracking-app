import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage } from './pages/Login'
import { DashboardPage } from './pages/Dashboard'
import { BoatsPage } from './pages/Boats'
import { BoatDetailPage } from './pages/BoatDetail'
import { VehiclesPage } from './pages/Vehicles'
import { ExpeditionsPage } from './pages/Expeditions'
import { TrackingPage } from './pages/Tracking'
import { AdminPage } from './pages/Admin'
import { FormPage } from './pages/Form'
import { DebugPage } from './pages/Debug'
import { NotFoundPage } from './pages/NotFound'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" />
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/track" element={<TrackingPage />} />
        <Route path="/track/:code" element={<TrackingPage />} />
        <Route path="/debug" element={<DebugPage />} />

        {/* Protected Routes */}
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        
        {/* Boats Routes */}
        <Route path="/boats" element={<ProtectedRoute><BoatsPage /></ProtectedRoute>} />
        <Route path="/boats/:id" element={<ProtectedRoute><BoatDetailPage /></ProtectedRoute>} />
        <Route path="/boats/new" element={<ProtectedRoute><FormPage type="boat" mode="create" /></ProtectedRoute>} />
        <Route path="/boats/:id/edit" element={<ProtectedRoute><FormPage type="boat" mode="edit" /></ProtectedRoute>} />

        {/* Vehicles Routes */}
        <Route path="/vehicles" element={<ProtectedRoute><VehiclesPage /></ProtectedRoute>} />
        <Route path="/vehicles/new" element={<ProtectedRoute><FormPage type="vehicle" mode="create" /></ProtectedRoute>} />
        <Route path="/vehicles/:id/edit" element={<ProtectedRoute><FormPage type="vehicle" mode="edit" /></ProtectedRoute>} />

        {/* Expeditions Routes */}
        <Route path="/expeditions" element={<ProtectedRoute><ExpeditionsPage /></ProtectedRoute>} />

        {/* Admin Routes */}
        <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />

        {/* Default Routes */}
        <Route path="/" element={<Navigate to="/dashboard" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
