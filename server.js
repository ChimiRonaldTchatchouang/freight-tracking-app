import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import jwt from 'jsonwebtoken'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3001

app.use(express.json())
app.use(cors())

// Mock data
const boats = [
  { id: '1', name: 'MS Neptune', imoNumber: '1234567890', capacityKg: 50000, status: 'disponible' },
  { id: '2', name: 'MS Atlantis', imoNumber: '0987654321', capacityKg: 45000, status: 'en_mer' }
]

const vehicles = [
  { id: '1', registrationPlate: 'ABC-1234', type: 'camion', weightEmptyKg: 5000, capacityKg: 20000, status: 'disponible' },
  { id: '2', registrationPlate: 'XYZ-5678', type: 'semi-remorque', weightEmptyKg: 8000, capacityKg: 30000, status: 'en_route' },
  { id: '3', registrationPlate: 'DEF-9999', type: 'fourgonnette', weightEmptyKg: 2000, capacityKg: 5000, status: 'maintenance' }
]

const JWT_SECRET = 'test-secret'

// API
app.get('/api/health', (req, res) => res.json({ status: 'ok' }))
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body
  if (email === 'admin@test.com' && password === 'test') {
    const token = jwt.sign({ email }, JWT_SECRET, { expiresIn: '24h' })
    res.json({ success: true, token, user: { email } })
  } else {
    res.status(401).json({ success: false, error: 'Invalid' })
  }
})

app.get('/api/boats', (req, res) => res.json(boats))
app.get('/api/vehicles', (req, res) => res.json(vehicles))

// Serve frontend
app.use(express.static(path.join(__dirname, 'frontend', 'dist')))
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
})

app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`)
})
