import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Layouts
import { MainLayout } from './components/layout/MainLayout'
import { PublicLayout } from './components/layout/PublicLayout'

// Pages
import { LoginPage } from './pages/auth/LoginAndLayout'
import { Dashboard } from './pages/dashboard/Dashboard'

// Boats
import { BoatsList } from './pages/boats/BoatsPages'
import { BoatForm } from './pages/boats/BoatsPages'
import { BoatDetail } from './pages/boats/BoatsPages'

// Vehicles
import { VehiclesList } from './pages/vehicles/VehiclesPages'
import { VehicleForm } from './pages/vehicles/VehiclesPages'
import { VehicleDetail } from './pages/vehicles/VehiclesPages'

// Expeditions
import { ExpeditionsList } from './pages/expeditions/ExpeditionsPages'
import { ExpeditionDetail } from './pages/expeditions/ExpeditionsPages'
import { ExpeditionWizard } from './pages/expeditions/ExpeditionsPages'

// Tracking (Public)
import { PublicTracking, QRScanner } from './pages/tracking/TrackingPages'

// Admin
import { AdminConfig } from './pages/admin/AdminPages'

// Errors
import { Error404, Error500 } from './pages/errors/ErrorPages'

const queryClient = new QueryClient()

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" />
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Auth Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            
            {/* Boats */}
            <Route path="/boats" element={<ProtectedRoute><BoatsList /></ProtectedRoute>} />
            <Route path="/boats/new" element={<ProtectedRoute><BoatForm /></ProtectedRoute>} />
            <Route path="/boats/:id" element={<ProtectedRoute><BoatDetail /></ProtectedRoute>} />
            <Route path="/boats/:id/edit" element={<ProtectedRoute><BoatForm /></ProtectedRoute>} />

            {/* Vehicles */}
            <Route path="/vehicles" element={<ProtectedRoute><VehiclesList /></ProtectedRoute>} />
            <Route path="/vehicles/new" element={<ProtectedRoute><VehicleForm /></ProtectedRoute>} />
            <Route path="/vehicles/:id" element={<ProtectedRoute><VehicleDetail /></ProtectedRoute>} />
            <Route path="/vehicles/:id/edit" element={<ProtectedRoute><VehicleForm /></ProtectedRoute>} />

            {/* Expeditions */}
            <Route path="/expeditions" element={<ProtectedRoute><ExpeditionsList /></ProtectedRoute>} />
            <Route path="/expeditions/new" element={<ProtectedRoute><ExpeditionWizard /></ProtectedRoute>} />
            <Route path="/expeditions/:id" element={<ProtectedRoute><ExpeditionDetail /></ProtectedRoute>} />

            {/* Admin */}
            <Route path="/admin/config" element={<ProtectedRoute><AdminConfig /></ProtectedRoute>} />
          </Route>

          {/* Public Routes (No Auth) */}
          <Route element={<PublicLayout />}>
            <Route path="/track" element={<PublicTracking />} />
            <Route path="/track/:code" element={<PublicTracking />} />
            <Route path="/track/scan" element={<QRScanner />} />
          </Route>

          {/* Error Routes */}
          <Route path="/404" element={<Error404 />} />
          <Route path="/500" element={<Error500 />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="*" element={<Navigate to="/404" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
