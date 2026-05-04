import { Router, Request, Response } from 'express'
import { PrismaClient } from '@prisma/client'

const router = Router()
const prisma = new PrismaClient()

// GET all boats
router.get('/', async (req: Request, res: Response) => {
  try {
    const status = req.query.status as string | undefined
    const boats = await prisma.boat.findMany({
      where: status ? { status } : undefined,
      orderBy: { createdAt: 'desc' }
    })
    res.json(boats)
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch boats' })
  }
})

// GET single boat
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const boat = await prisma.boat.findUnique({
      where: { id: req.params.id }
    })
    if (!boat) {
      return res.status(404).json({ error: 'Boat not found' })
    }
    res.json(boat)
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch boat' })
  }
})

// POST create boat
router.post('/', async (req: Request, res: Response) => {
  try {
    const { name, imoNumber, capacityKg, portDeparture, portArrival } = req.body

    if (!name || !imoNumber || !capacityKg) {
      return res.status(400).json({ error: 'Missing required fields' })
    }

    const boat = await prisma.boat.create({
      data: {
        name,
        imoNumber,
        capacityKg: parseInt(capacityKg),
        portDeparture,
        portArrival,
        status: 'en_equipement'
      }
    })

    res.status(201).json(boat)
  } catch (error: any) {
    if (error.code === 'P2002') {
      return res.status(400).json({ error: 'Boat with this IMO already exists' })
    }
    res.status(500).json({ error: 'Failed to create boat' })
  }
})

// PUT update boat
router.put('/:id', async (req: Request, res: Response) => {
  try {
    const { name, capacityKg, portDeparture, portArrival } = req.body

    const boat = await prisma.boat.update({
      where: { id: req.params.id },
      data: {
        ...(name && { name }),
        ...(capacityKg && { capacityKg: parseInt(capacityKg) }),
        ...(portDeparture && { portDeparture }),
        ...(portArrival && { portArrival })
      }
    })

    res.json(boat)
  } catch (error: any) {
    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Boat not found' })
    }
    res.status(500).json({ error: 'Failed to update boat' })
  }
})

// DELETE boat
router.delete('/:id', async (req: Request, res: Response) => {
  try {
    const expeditions = await prisma.expedition.findMany({
      where: {
        boatId: req.params.id,
        status: { not: 'livrée' }
      }
    })

    if (expeditions.length > 0) {
      return res.status(400).json({ error: 'Cannot delete boat with active expeditions' })
    }

    await prisma.boat.delete({
      where: { id: req.params.id }
    })

    res.json({ success: true })
  } catch (error: any) {
    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Boat not found' })
    }
    res.status(500).json({ error: 'Failed to delete boat' })
  }
})

export default router
