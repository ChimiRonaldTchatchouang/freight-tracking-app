"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const router = express_1.default.Router();
// Mock data
const boats = [
    { id: '1', name: 'MS Neptune', imoNumber: '1234567890', capacityKg: 50000, portDeparture: 'Port of LA', portArrival: 'Port of Rotterdam', status: 'disponible' },
    { id: '2', name: 'MS Atlantis', imoNumber: '0987654321', capacityKg: 45000, portDeparture: 'Port of Singapore', portArrival: 'Port of Hamburg', status: 'en_mer' }
];
// GET all boats
router.get('/', (req, res) => {
    res.json(boats);
});
// GET boat by ID
router.get('/:id', (req, res) => {
    const boat = boats.find(b => b.id === req.params.id);
    if (!boat)
        return res.status(404).json({ error: 'Boat not found' });
    res.json(boat);
});
// POST create boat
router.post('/', (req, res) => {
    try {
        const { name, imoNumber, capacityKg, portDeparture, portArrival } = req.body;
        if (!name || !imoNumber || !capacityKg) {
            return res.status(400).json({ error: 'Missing required fields' });
        }
        const newBoat = {
            id: String(boats.length + 1),
            name,
            imoNumber,
            capacityKg: Number(capacityKg),
            portDeparture: portDeparture || '',
            portArrival: portArrival || '',
            status: 'disponible'
        };
        boats.push(newBoat);
        res.status(201).json(newBoat);
    }
    catch (error) {
        res.status(500).json({ error: 'Internal server error' });
    }
});
// PUT update boat
router.put('/:id', (req, res) => {
    try {
        const boat = boats.find(b => b.id === req.params.id);
        if (!boat)
            return res.status(404).json({ error: 'Boat not found' });
        const updated = { ...boat, ...req.body };
        const index = boats.findIndex(b => b.id === req.params.id);
        boats[index] = updated;
        res.json(updated);
    }
    catch (error) {
        res.status(500).json({ error: 'Internal server error' });
    }
});
// DELETE boat
router.delete('/:id', (req, res) => {
    try {
        const index = boats.findIndex(b => b.id === req.params.id);
        if (index === -1)
            return res.status(404).json({ error: 'Boat not found' });
        const deleted = boats.splice(index, 1);
        res.json(deleted[0]);
    }
    catch (error) {
        res.status(500).json({ error: 'Internal server error' });
    }
});
exports.default = router;
//# sourceMappingURL=boats.js.map