import express, { Request, Response } from 'express'

const router = express.Router()

// Mock data
const vehicles = [
  { id: '1', registrationPlate: 'ABC-1234', type: 'camion', weightEmptyKg: 5000, capacityKg: 20000, status: 'disponible' },
  { id: '2', registrationPlate: 'XYZ-5678', type: 'semi-remorque', weightEmptyKg: 8000, capacityKg: 30000, status: 'en_route' },
  { id: '3', registrationPlate: 'DEF-9999', type: 'fourgonnette', weightEmptyKg: 2000, capacityKg: 5000, status: 'maintenance' }
]

// GET all vehicles
router.get('/', (req: Request, res: Response) => {
  res.json(vehicles)
})

// GET vehicle by ID
router.get('/:id', (req: Request, res: Response) => {
  const vehicle = vehicles.find(v => v.id === req.params.id)
  if (!vehicle) return res.status(404).json({ error: 'Vehicle not found' })
  res.json(vehicle)
})

// POST create vehicle
router.post('/', (req: Request, res: Response) => {
  try {
    const { registrationPlate, type, weightEmptyKg, capacityKg } = req.body

    if (!registrationPlate || !type || !weightEmptyKg || !capacityKg) {
      return res.status(400).json({ error: 'Missing required fields' })
    }

    const newVehicle = {
      id: String(vehicles.length + 1),
      registrationPlate,
      type,
      weightEmptyKg: Number(weightEmptyKg),
      capacityKg: Number(capacityKg),
      status: 'disponible'
    }

    vehicles.push(newVehicle)
    res.status(201).json(newVehicle)
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' })
  }
})

// PUT update vehicle
router.put('/:id', (req: Request, res: Response) => {
  try {
    const vehicle = vehicles.find(v => v.id === req.params.id)
    if (!vehicle) return res.status(404).json({ error: 'Vehicle not found' })

    const updated = { ...vehicle, ...req.body }
    const index = vehicles.findIndex(v => v.id === req.params.id)
    vehicles[index] = updated

    res.json(updated)
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' })
  }
})

// DELETE vehicle
router.delete('/:id', (req: Request, res: Response) => {
  try {
    const index = vehicles.findIndex(v => v.id === req.params.id)
    if (index === -1) return res.status(404).json({ error: 'Vehicle not found' })

    const deleted = vehicles.splice(index, 1)
    res.json(deleted[0])
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' })
  }
})

export default router
