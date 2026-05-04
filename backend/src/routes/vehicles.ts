import { Router, Request, Response } from 'express'
import { PrismaClient } from '@prisma/client'

const router = Router()
const prisma = new PrismaClient()

router.get('/', async (req: Request, res: Response) => {
  try {
    const vehicles = await prisma.vehicle.findMany({
      orderBy: { createdAt: 'desc' }
    })
    res.json(vehicles)
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch vehicles' })
  }
})

router.get('/:id', async (req: Request, res: Response) => {
  try {
    const vehicle = await prisma.vehicle.findUnique({
      where: { id: req.params.id }
    })
    if (!vehicle) return res.status(404).json({ error: 'Vehicle not found' })
    res.json(vehicle)
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch vehicle' })
  }
})

router.post('/', async (req: Request, res: Response) => {
  try {
    const { registrationPlate, type, weightEmptyKg, capacityKg } = req.body

    if (!registrationPlate || !type || !capacityKg) {
      return res.status(400).json({ error: 'Missing required fields' })
    }

    const vehicle = await prisma.vehicle.create({
      data: {
        registrationPlate,
        type,
        weightEmptyKg: parseInt(weightEmptyKg),
        capacityKg: parseInt(capacityKg),
        status: 'disponible'
      }
    })

    res.status(201).json(vehicle)
  } catch (error: any) {
    if (error.code === 'P2002') {
      return res.status(400).json({ error: 'Vehicle with this registration already exists' })
    }
    res.status(500).json({ error: 'Failed to create vehicle' })
  }
})

router.put('/:id', async (req: Request, res: Response) => {
  try {
    const { type, weightEmptyKg, capacityKg } = req.body

    const vehicle = await prisma.vehicle.update({
      where: { id: req.params.id },
      data: {
        ...(type && { type }),
        ...(weightEmptyKg && { weightEmptyKg: parseInt(weightEmptyKg) }),
        ...(capacityKg && { capacityKg: parseInt(capacityKg) })
      }
    })

    res.json(vehicle)
  } catch (error: any) {
    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Vehicle not found' })
    }
    res.status(500).json({ error: 'Failed to update vehicle' })
  }
})

router.delete('/:id', async (req: Request, res: Response) => {
  try {
    await prisma.vehicle.delete({
      where: { id: req.params.id }
    })
    res.json({ success: true })
  } catch (error: any) {
    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Vehicle not found' })
    }
    res.status(500).json({ error: 'Failed to delete vehicle' })
  }
})

export default router
