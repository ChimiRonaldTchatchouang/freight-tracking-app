import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('Seeding database...')

  // Seed a boat
  const boat = await prisma.boat.create({
    data: {
      name: 'MS Neptune',
      imoNumber: '1234567890',
      capacityKg: 50000,
      portDeparture: 'Port of Los Angeles',
      portArrival: 'Port of Rotterdam',
      status: 'disponible'
    }
  })

  console.log('Created boat:', boat)

  // Seed a vehicle
  const vehicle = await prisma.vehicle.create({
    data: {
      registrationPlate: 'ABC-1234',
      type: 'camion',
      weightEmptyKg: 5000,
      capacityKg: 20000,
      status: 'disponible'
    }
  })

  console.log('Created vehicle:', vehicle)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
