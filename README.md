# 🚢 Freight Tracking Application

Maritime freight management application with real-time tracking and automatic deployment.

## 📋 Project Structure

```
freight-tracking-app/
├── backend/          # Node.js API (Express + Prisma)
├── frontend/         # React application (Vite + TailwindCSS)
├── docker-compose.yml
├── README.md
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Docker & Docker Compose
- Git

### Development Setup

```bash
# Clone repository
git clone https://github.com/ChimiRonaldTchatchouang/freight-tracking-app.git
cd freight-tracking-app

# Start Docker services
docker-compose up -d

# Backend setup
cd backend
npm install
npx prisma migrate dev --name init
npm run dev

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:3000
- Backend: http://localhost:3001
- Health Check: http://localhost:3001/health

## 📁 API Endpoints

### Boats
- `GET /api/v1/boats` - List all boats
- `GET /api/v1/boats/:id` - Get boat details
- `POST /api/v1/boats` - Create boat
- `PUT /api/v1/boats/:id` - Update boat
- `DELETE /api/v1/boats/:id` - Delete boat

### Vehicles
- `GET /api/v1/vehicles` - List all vehicles
- `GET /api/v1/vehicles/:id` - Get vehicle details
- `POST /api/v1/vehicles` - Create vehicle
- `PUT /api/v1/vehicles/:id` - Update vehicle
- `DELETE /api/v1/vehicles/:id` - Delete vehicle

## 🔐 Environment Variables

Create `.env` files based on `.env.example`:

### Backend (.env)
```
DATABASE_URL="postgresql://freight_user:freight_password@localhost:5432/freight_dev"
NODE_ENV="development"
PORT=3001
JWT_SECRET="your-secret-key"
SENDGRID_API_KEY="your-sendgrid-key"
FRONTEND_URL="http://localhost:3000"
```

### Frontend (.env)
```
VITE_API_URL="http://localhost:3001"
VITE_APP_NAME="Freight Tracking App"
```

## 🧪 Testing

```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd frontend
npm test
```

## 🔨 Build for Production

```bash
# Backend
cd backend
npm run build

# Frontend
cd frontend
npm run build
```

## 📦 Deployment

### Vercel (Frontend)
1. Push code to GitHub
2. Import repository to Vercel
3. Set `VITE_API_URL` environment variable
4. Deploy

### Railway (Backend)
1. Push code to GitHub
2. Create new service in Railway
3. Connect to GitHub repository
4. Set environment variables
5. Deploy

## 📚 Tech Stack

### Backend
- Node.js 18+ with Express.js
- Prisma ORM
- PostgreSQL
- TypeScript
- JWT Authentication

### Frontend
- React 18
- Vite
- TypeScript
- TailwindCSS
- React Query
- Zustand

## 📝 License

MIT

## 👨‍💻 Author

Chimi Ronald Tchatchouang

---

For more information, see the full documentation in `/docs`
