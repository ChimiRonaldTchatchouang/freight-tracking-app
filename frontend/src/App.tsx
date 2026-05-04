import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Simple pages
function Dashboard() {
  return <div className="p-6"><h1 className="text-3xl font-bold">Dashboard</h1></div>
}

function LoginPage() {
  return <div className="p-6"><h1>Login</h1></div>
}

function BoatsList() {
  return <div className="p-6"><h1>Boats List</h1></div>
}

function NotFound() {
  return <div className="p-6"><h1 className="text-3xl">404 - Not Found</h1></div>
}

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
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/boats" element={<ProtectedRoute><BoatsList /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
