# Web Version Architecture

## Goals
- Browser-based STLoop (no installation)
- Code generation via LLM API
- Optional: In-browser west build via WebContainer

## Tech Stack
- **Frontend**: React + Vite (pure browser)
- **Build Environment**: WebContainer (StackBlitz) or None
- **LLM**: Direct API calls or via proxy

## Limitations
| Feature | Desktop (Tauri) | Web |
|---------|----------------|-----|
| Code Generation | ✅ | ✅ |
| west build | ✅ | ⚠️ WebContainer? |
| west flash | ✅ | ❌ (no USB access) |
| Renode sim | ✅ | ❌ |
| File System | ✅ | ✅ (OPFS/IndexedDB) |

## Architecture

### Option A: Full WebContainer (Experimental)
```
Browser
├── React UI
├── WebContainer (Node.js in browser)
│   ├── Zephyr SDK (~50MB download)
│   ├── west build
│   └── zephyr.elf output
└── LLM API calls
```

### Option B: Hybrid (Recommended)
```
Browser
├── React UI
├── Code Editor
├── Project files (OPFS)
└── LLM API calls

Desktop Agent (optional)
├── File sync from browser
├── west build
└── west flash
```

### Option C: Minimal (Static Site)
```
Browser
├── React UI
├── Code generation only
└── Export project as ZIP

User downloads and builds locally
```

## Recommendation
Start with **Option C** (minimal) for MVP:
1. Fastest to implement
2. No complex infrastructure
3. User can still download and build locally
4. Can upgrade to Option A/B later

Then implement **Option A** if WebContainer proves feasible.
