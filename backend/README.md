# AETHER – Autonomous Constellation Manager

Backend service for autonomous satellite constellation management, orbit propagation, and mission planning.

## Tech Stack

- **Framework:** FastAPI
- **Runtime:** Python 3.11
- **Key Libraries:** NumPy, SciPy, Astropy, Poliastro

## Run Locally

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m app.main
```

The API will be available at `http://localhost:8000`.
Interactive docs are served at `http://localhost:8000/docs`.

### Verify

```bash
curl http://localhost:8000/api/health
```

## Run with Docker

```bash
cd backend

# Build the image
docker build -t aether-backend .

# Run the container
docker run -p 8000:8000 aether-backend
```
