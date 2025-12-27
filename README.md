# 🚢 Navix-AI

**HACOPSO-Powered Carbon-Aware Maritime Route Optimization Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Navix-AI is a production-grade backend for multi-objective maritime route optimization. It uses a research-grade **Hybrid Adaptive Chaotic Opposition-Based Particle Swarm Optimization (HACOPSO)** algorithm to compute Pareto-optimal ship routes that minimize:

- ⛽ **Fuel Consumption**
- ⏱️ **Travel Time**
- 🌊 **Storm & Piracy Risk**
- 🌱 **Carbon Emissions**
- 🛳️ **Wave Resistance (Comfort)**

---

## ✨ Features

### 🧠 HACOPSO Optimization Engine
- **Chaotic Inertia Weight Scheduling**: Logistic, tent, and sinusoidal maps for dynamic adaptation
- **Opposition-Based Learning**: Enhanced exploration via opposition population initialization
- **Multi-Objective Pareto Archive**: Non-dominated sorting with crowding distance
- **Constraint Handling**: Land, storm, piracy, depth, and speed constraints
- **GPU-Ready Structure**: NumPy vectorized operations

### 🌊 Digital Ocean Grid
- Time-indexed environmental layers
- Wave, current, storm, and piracy data
- Dynamic grid interpolation
- Resistance factor calculation

### 🚢 Ship Intelligence Profiles
- Hull drag curves (Holtrop-Mennen style)
- Speed-fuel consumption models
- IMO-compliant emission factors (CO2, SOx, NOx, PM)
- CII rating calculation

### 💾 Route Memory Bank
- Versioned best routes storage
- Fréchet distance similarity detection
- Warm-start optimization

### 🔍 Explainable AI Layer
- Route trade-off decomposition
- Sensitivity analysis
- "Why this route?" API

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or poetry

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/navix-ai.git
cd navix-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Seed the database
python -m data.seed

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
# Build and run
docker-compose up --build

# The API is available at http://localhost:8000
```

### Deploy to Render (Free Tier)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/navix-ai.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com) and sign up/login
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` blueprint
   - Or configure manually:
     - **Runtime**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Click **Create Web Service**

3. **Your API will be live at**: `https://navix-ai.onrender.com`

> **Note**: Free tier has cold starts (first request after 15min inactivity takes ~30s).

---

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/optimize` | Submit route optimization job |
| `GET` | `/jobs/{job_id}` | Get job status |
| `GET` | `/routes/{job_id}` | Get Pareto-optimal routes |
| `GET` | `/explain/{route_id}` | Get route explanation |
| `GET` | `/benchmark` | Compare HACOPSO vs GA |
| `GET` | `/map/layers` | Get available map layers |

### Example: Submit Optimization

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "origin_locode": "SGSIN",
    "destination_locode": "NLRTM",
    "ship_id": "container_large",
    "algorithm": "hacopso",
    "weights": {
      "fuel": 0.3,
      "time": 0.25,
      "risk": 0.2,
      "emissions": 0.15,
      "comfort": 0.1
    }
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Optimization job submitted. Algorithm: hacopso",
  "estimated_time_seconds": 100
}
```

### Check Job Status

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

### Get Routes

```bash
curl http://localhost:8000/routes/550e8400-e29b-41d4-a716-446655440000
```

---

## 🏗️ Architecture

```
navix-ai/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                 # Configuration & database
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── engine/               # HACOPSO & GA engines
│   ├── ocean/                # Digital ocean grid
│   ├── ship/                 # Ship profiles & emissions
│   ├── memory/               # Route memory bank
│   ├── explain/              # Explainability layer
│   ├── services/             # Business logic
│   └── api/                  # REST endpoints
├── data/
│   └── seed.py               # Sample data
├── tests/                    # Unit & integration tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🔧 Configuration

Configuration is managed via environment variables. See `.env.example` for all options.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./navix.db` | Database connection |
| `HACOPSO_SWARM_SIZE` | `50` | Particle swarm size |
| `HACOPSO_MAX_ITERATIONS` | `200` | Maximum iterations |
| `HACOPSO_CHAOS_TYPE` | `logistic` | Chaos map type |
| `RATE_LIMIT_REQUESTS` | `100` | Requests per period |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_hacopso.py -v
```

---

## 📊 Benchmark

Compare HACOPSO against genetic algorithm:

```bash
curl http://localhost:8000/benchmark
```

Response:
```json
{
  "hacopso": {
    "algorithm": "HACOPSO",
    "iterations": 50,
    "execution_time_seconds": 2.34,
    "archive_size": 15,
    "best_fuel": 245.6,
    "best_time": 312.4
  },
  "ga": {
    "algorithm": "GA (NSGA-II)",
    "iterations": 50,
    "execution_time_seconds": 3.12,
    "archive_size": 12,
    "best_fuel": 267.8,
    "best_time": 298.1
  },
  "winner": "HACOPSO",
  "improvement_pct": 8.5
}
```

---

## 🗺️ Map Layers

Get environmental data for visualization:

```bash
# Get available layers
curl http://localhost:8000/map/layers

# Get storm zones
curl http://localhost:8000/map/layer/storm

# Get piracy zones
curl http://localhost:8000/map/layer/piracy
```

---

## 📖 HACOPSO Algorithm

The Hybrid Adaptive Chaotic Opposition-Based PSO combines:

1. **Chaotic Inertia Weight**: Uses logistic map for dynamic exploration/exploitation balance
   ```
   x_{n+1} = 4 * x_n * (1 - x_n)
   w = w_max - (w_max - w_min) * t/T * (1 + 0.5 * (chaos - 0.5))
   ```

2. **Opposition-Based Learning**: Generates opposing solutions for better coverage
   ```
   x_opp = lb + ub - x
   ```

3. **Pareto Archive**: Maintains non-dominated solutions with crowding distance

4. **Constraint Handling**: Penalty functions for infeasible routes

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- IMO for emission factor guidelines
- Maritime industry data standards (UN/LOCODE)
- Research papers on HACOPSO and multi-objective optimization

---

**Built with ❤️ for sustainable maritime shipping**
