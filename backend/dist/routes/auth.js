"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const router = express_1.default.Router();
// Mock users (dans une vraie app, ce serait la DB)
const users = [
    { id: '1', email: 'admin@freight-tracking.com', password: 'Admin123!@#', role: 'ADMIN' },
    { id: '2', email: 'user@freight-tracking.com', password: 'User123!@#', role: 'USER' },
    { id: '3', email: 'transitaire@freight-tracking.com', password: 'Transitaire123!@#', role: 'TRANSITAIRE' }
];
// Login endpoint
router.post('/login', (req, res) => {
    try {
        const { email, password } = req.body;
        // Validation
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password required' });
        }
        // Find user
        const user = users.find(u => u.email === email && u.password === password);
        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        // Generate JWT token
        const token = jsonwebtoken_1.default.sign({ id: user.id, email: user.email, role: user.role }, process.env.JWT_SECRET || 'default-secret-key-change-in-prod', { expiresIn: '24h' });
        // Return token and user
        res.json({
            token,
            user: {
                id: user.id,
                email: user.email,
                role: user.role
            }
        });
    }
    catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// Register endpoint (optional)
router.post('/register', (req, res) => {
    try {
        const { email, password, role } = req.body;
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password required' });
        }
        // Check if user exists
        if (users.find(u => u.email === email)) {
            return res.status(409).json({ error: 'User already exists' });
        }
        // Create new user
        const newUser = {
            id: String(users.length + 1),
            email,
            password,
            role: role || 'USER'
        };
        users.push(newUser);
        // Generate token
        const token = jsonwebtoken_1.default.sign({ id: newUser.id, email: newUser.email, role: newUser.role }, process.env.JWT_SECRET || 'default-secret-key-change-in-prod', { expiresIn: '24h' });
        res.status(201).json({
            token,
            user: {
                id: newUser.id,
                email: newUser.email,
                role: newUser.role
            }
        });
    }
    catch (error) {
        console.error('Register error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// Verify token endpoint
router.post('/verify', (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }
        const decoded = jsonwebtoken_1.default.verify(token, process.env.JWT_SECRET || 'default-secret-key-change-in-prod');
        res.json({ valid: true, user: decoded });
    }
    catch (error) {
        res.status(401).json({ error: 'Invalid token' });
    }
});
exports.default = router;
//# sourceMappingURL=auth.js.map