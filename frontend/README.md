# NaviX-AI Frontend

**HACOPSO-Powered Maritime Route Optimization UI**

A sleek, ultra-modern React frontend for the NaviX-AI maritime routing platform.

## Features

- 🌊 **Animated Ocean Background** - Three.js WebGL water surface
- 🗺️ **Interactive Map** - Mapbox GL with route visualization
- 📊 **Pareto Front Explorer** - Interactive scatter charts
- 📈 **Live Dashboard** - Fleet & emissions analytics
- 🔍 **Explainable AI** - "Why this route?" analysis
- ✨ **Glassmorphism UI** - Dark ocean theme

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your Mapbox token and API URL
# Get Mapbox token at: https://mapbox.com

# Start dev server
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (e.g., `https://navix-ai.onrender.com`) |
| `VITE_MAPBOX_TOKEN` | Mapbox public access token |

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with animated hero |
| `/optimize` | Route optimizer with map & sliders |
| `/job/:id` | Live optimization progress |
| `/routes/:id` | Pareto front explorer |
| `/dashboard` | Fleet & emissions dashboard |
| `/explain/:id` | Explainable AI view |

## Deploy to Vercel

1. Push to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import repository
4. Add environment variables:
   - `VITE_API_URL` = your Render backend URL
   - `VITE_MAPBOX_TOKEN` = your Mapbox token
5. Deploy!

## Tech Stack

- Vite + React + TypeScript
- TailwindCSS + Framer Motion
- Mapbox GL JS
- Three.js + React Three Fiber
- Recharts
- Axios
