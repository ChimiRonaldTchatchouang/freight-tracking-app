"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const router = express_1.default.Router();
const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key-change-in-prod';
// Mock users database
const users = [
    {
        id: '1',
        email: 'admin@freight-tracking.com',
        password: 'Admin123!@#',
        role: 'ADMIN',
        name: 'Admin User'
    },
    {
        id: '2',
        email: 'user@freight-tracking.com',
        password: 'User123!@#',
        role: 'USER',
        name: 'Standard User'
    },
    {
        id: '3',
        email: 'transitaire@freight-tracking.com',
        password: 'Transitaire123!@#',
        role: 'TRANSITAIRE',
        name: 'Transitaire User'
    }
];
// Login endpoint
router.post('/login', (req, res) => {
    try {
        console.log('📨 Login request received');
        const { email, password } = req.body;
        // Validation
        if (!email || !password) {
            console.log('⚠️ Missing email or password');
            return res.status(400).json({
                success: false,
                error: 'Email and password required'
            });
        }
        console.log(`🔍 Searching for user: ${email}`);
        // Find user
        const user = users.find(u => u.email === email && u.password === password);
        if (!user) {
            console.log(`❌ User not found or password incorrect: ${email}`);
            return res.status(401).json({
                success: false,
                error: 'Invalid email or password'
            });
        }
        console.log(`✅ User found: ${user.email}`);
        // Generate JWT token
        const token = jsonwebtoken_1.default.sign({
            id: user.id,
            email: user.email,
            role: user.role,
            name: user.name
        }, JWT_SECRET, { expiresIn: '24h' });
        console.log(`✅ Token generated`);
        // Return response
        const response = {
            success: true,
            token,
            user: {
                id: user.id,
                email: user.email,
                role: user.role,
                name: user.name
            }
        };
        console.log(`✅ Sending response`);
        res.status(200).json(response);
    }
    catch (error) {
        console.error('❌ Login error:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            message: error.message
        });
    }
});
// Register endpoint (optional)
router.post('/register', (req, res) => {
    try {
        const { email, password, name, role } = req.body;
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                error: 'Email and password required'
            });
        }
        // Check if user exists
        if (users.find(u => u.email === email)) {
            return res.status(409).json({
                success: false,
                error: 'User already exists'
            });
        }
        // Create new user
        const newUser = {
            id: String(users.length + 1),
            email,
            password,
            role: role || 'USER',
            name: name || email
        };
        users.push(newUser);
        // Generate token
        const token = jsonwebtoken_1.default.sign({ id: newUser.id, email: newUser.email, role: newUser.role, name: newUser.name }, JWT_SECRET, { expiresIn: '24h' });
        res.status(201).json({
            success: true,
            token,
            user: {
                id: newUser.id,
                email: newUser.email,
                role: newUser.role,
                name: newUser.name
            }
        });
    }
    catch (error) {
        console.error('Register error:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error'
        });
    }
});
// Verify token endpoint
router.post('/verify', (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        if (!token) {
            return res.status(401).json({
                success: false,
                error: 'No token provided'
            });
        }
        const decoded = jsonwebtoken_1.default.verify(token, JWT_SECRET);
        res.json({
            success: true,
            valid: true,
            user: decoded
        });
    }
    catch (error) {
        console.error('Verify error:', error);
        res.status(401).json({
            success: false,
            valid: false,
            error: 'Invalid token'
        });
    }
});
// Get current user
router.get('/me', (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        if (!token) {
            return res.status(401).json({
                success: false,
                error: 'No token provided'
            });
        }
        const decoded = jsonwebtoken_1.default.verify(token, JWT_SECRET);
        res.json({
            success: true,
            user: decoded
        });
    }
    catch (error) {
        res.status(401).json({
            success: false,
            error: 'Invalid token'
        });
    }
});
exports.default = router;
//# sourceMappingURL=auth.js.map