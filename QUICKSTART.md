# Fightcraft - Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start the AI Backend

**Windows:**
```bash
start_backend.bat
```

**Linux/Mac:**
```bash
python ai_backend/server.py
```

Wait for the message: "Server will be available at http://localhost:8000"

## Step 3: Start the Game

Open a **new terminal window** and run:

**Windows:**
```bash
start_game.bat
```

**Linux/Mac:**
```bash
python main.py
```

## Step 4: Play!

### Crafting:
1. **Drag 3 materials** from inventory to the 3x3 crafting grid
2. Click **"Craft Item"** button
3. Wait 2-3 seconds for AI generation
4. **Drag result** to equipment slots (Weapon/Armor/Buff)
5. Press **ESC** to start combat

### Combat:
1. Press **SPACE** to execute each turn
2. Press **A** to enable auto-combat
3. Watch your crafted items in action!
4. Press **ESC** to return to crafting

## Try These Recipes:

**Powerful Weapon:**
- Iron Ingot + Oak Wood + Crystal Shard

**Strong Armor:**
- Dragon Scale + Gold Bar + Crystal Shard

**Health Buff:**
- Magic Essence + Crystal Shard + Dragon Scale

## Troubleshooting

**"AI Backend offline"**:
- Make sure you started the backend first (Step 2)
- The game will still work with fallback generation

**Game runs slow**:
- Close other programs
- Backend caches generated items for instant reuse

**Need help?**:
- See [README.md](README.md) for full documentation
- Check backend logs in the terminal

---

**That's it! Have fun crafting and fighting!** 🎮⚔️
