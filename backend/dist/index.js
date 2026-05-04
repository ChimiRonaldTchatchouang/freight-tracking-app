"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const helmet_1 = __importDefault(require("helmet"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3001;
// Middleware
app.use((0, helmet_1.default)());
app.use((0, cors_1.default)({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true
}));
app.use(express_1.default.json());
// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        message: 'Backend is running!'
    });
});
// Auth routes
app.use('/api/v1/auth', require('./routes/auth').default);
// Boats routes
app.use('/api/v1/boats', require('./routes/boats').default);
// Vehicles routes
app.use('/api/v1/vehicles', require('./routes/vehicles').default);
// Default routes for testing
app.get('/', (req, res) => {
    res.json({
        message: 'Freight Tracking API',
        version: '1.0.0',
        endpoints: {
            health: '/health',
            auth: '/api/v1/auth/login',
            boats: '/api/v1/boats',
            vehicles: '/api/v1/vehicles'
        }
    });
});
// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Route not found' });
});
// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(500).json({ error: 'Internal server error', message: err.message });
});
const server = app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📍 Health check: http://localhost:${PORT}/health`);
    console.log(`🔐 Login: POST http://localhost:${PORT}/api/v1/auth/login`);
    console.log(`✅ API is ready!`);
});
exports.default = app;
//# sourceMappingURL=index.js.map