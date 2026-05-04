import express, { Request, Response } from 'express'
import cors from 'cors'
import helmet from 'helmet'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'

console.log(`🚀 Starting server...`)
console.log(`📍 FRONTEND_URL: ${FRONTEND_URL}`)
console.log(`📍 PORT: ${PORT}`)

// Middleware - Security & CORS
app.use(helmet())

// CORS Configuration
app.use(cors({
  origin: [
    FRONTEND_URL,
    'http://localhost:3000',
    'http://localhost:5173',
    /\.vercel\.app$/,
    /\.railway\.app$/
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))

// Body parser
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// Request logging
app.use((req: Request, res: Response, next: express.NextFunction) => {
  console.log(`${req.method} ${req.path}`)
  next()
})

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    message: 'Backend is running!',
    frontend_url: FRONTEND_URL
  })
})

// Home route
app.get('/', (req: Request, res: Response) => {
  res.json({
    message: 'Freight Tracking API',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      auth: {
        login: 'POST /api/v1/auth/login',
        register: 'POST /api/v1/auth/register',
        verify: 'POST /api/v1/auth/verify'
      },
      boats: 'GET /api/v1/boats',
      vehicles: 'GET /api/v1/vehicles'
    }
  })
})

// Auth routes
app.use('/api/v1/auth', require('./routes/auth').default)

// Boats routes
app.use('/api/v1/boats', require('./routes/boats').default)

// Vehicles routes
app.use('/api/v1/vehicles', require('./routes/vehicles').default)

// 404 handler
app.use((req: Request, res: Response) => {
  console.log(`⚠️ 404: ${req.method} ${req.path}`)
  res.status(404).json({
    error: 'Route not found',
    path: req.path,
    method: req.method
  })
})

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('❌ Error:', err)
  res.status(err.status || 500).json({
    error: 'Internal server error',
    message: err.message,
    stack: process.env.NODE_ENV === 'production' ? undefined : err.stack
  })
})

const server = app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`)
  console.log(`📍 Health check: http://localhost:${PORT}/health`)
  console.log(`🔐 Login: POST http://localhost:${PORT}/api/v1/auth/login`)
  console.log(`✅ API is ready!`)
})

export default app
