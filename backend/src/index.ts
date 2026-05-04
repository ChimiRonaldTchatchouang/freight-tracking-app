import express, { Request, Response } from 'express'
import cors from 'cors'
import helmet from 'helmet'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001

// Middleware
app.use(helmet())
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}))
app.use(express.json())

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    message: 'Backend is running!'
  })
})

// Auth routes
app.use('/api/v1/auth', require('./routes/auth').default)

// Boats routes
app.use('/api/v1/boats', require('./routes/boats').default)

// Vehicles routes
app.use('/api/v1/vehicles', require('./routes/vehicles').default)

// Default routes for testing
app.get('/', (req: Request, res: Response) => {
  res.json({ 
    message: 'Freight Tracking API',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      auth: '/api/v1/auth/login',
      boats: '/api/v1/boats',
      vehicles: '/api/v1/vehicles'
    }
  })
})

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: 'Route not found' })
})

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err)
  res.status(500).json({ error: 'Internal server error', message: err.message })
})

const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`)
  console.log(`📍 Health check: http://localhost:${PORT}/health`)
  console.log(`🔐 Login: POST http://localhost:${PORT}/api/v1/auth/login`)
  console.log(`✅ API is ready!`)
})

export default app
