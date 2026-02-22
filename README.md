# AI-Based Crop Disease Detector

An end-to-end crop disease detection platform using:
- `React + Vite` for frontend
- `Spring Boot + MongoDB` for backend APIs and history storage
- `FastAPI + TensorFlow` for image-based disease prediction

## Features

- Upload leaf image and get disease prediction
- Clean disease names (for example `Late Blight` instead of class IDs)
- Dynamic severity and treatment recommendations
- Top 3 predictions with confidence scores and progress bars
- Step-by-step treatment plan cards
- Scan history timeline
- History export to CSV
- Clear history with confirmation modal
- Server-side history persistence (`MongoDB`) with frontend fallback cache

## Project Structure

```text
AI-Based-Crop-Disease-Detector/
  ai-service/         # FastAPI + TensorFlow prediction service
  backend/            # Spring Boot REST API + MongoDB
  frontend/           # React Vite frontend
  database/           # (optional local db assets, if any)
```

## Tech Stack

- Frontend: React 19, Vite 7, Tailwind CSS
- Backend: Java 17, Spring Boot 3, Spring Data MongoDB
- AI Service: Python 3.10, FastAPI, TensorFlow, Pillow, NumPy
- Database: MongoDB

## Prerequisites

- Node.js 18+
- Java 17+
- Maven (or use `mvnw.cmd` in project)
- Python 3.10
- MongoDB running on `localhost:27017`

## 1) Setup AI Service

From project root:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install fastapi "uvicorn[standard]" tensorflow pillow numpy h5py python-multipart
```

Place your trained model file at:

- `ai-service/model.h5`

Run AI service:

```powershell
python -m uvicorn predict:app --host 127.0.0.1 --port 8000 --app-dir ai-service
```

Health check:

```powershell
curl http://127.0.0.1:8000/
```

## 2) Setup Backend (Spring Boot)

Backend config file:
- `backend/src/main/resources/application.properties`

Default values:
- `server.port=8080`
- `spring.data.mongodb.uri=mongodb://localhost:27017/cropdisease`
- `ai.service.url=http://127.0.0.1:8000/predict`

Run backend:

```powershell
cd backend
.\mvnw.cmd spring-boot:run
```

Run tests:

```powershell
.\mvnw.cmd test -q
```

## 3) Setup Frontend (React)

Run frontend:

```powershell
cd frontend
npm install
npm run dev
```

Build frontend:

```powershell
npm run build
```

Frontend dev server uses `/api` proxy to backend (`localhost:8080`).

## API Endpoints

### Auth
- `POST /api/auth/register`

### Prediction
- `POST /api/predict` (multipart form-data with field `file`)

### Scan History
- `GET /api/scans` -> list recent scans
- `POST /api/scans` -> save a scan entry
- `DELETE /api/scans` -> clear scan history

## Common Issues

### `AI service is unavailable`
- Ensure FastAPI is running on `127.0.0.1:8000`
- Verify `ai.service.url` in `backend/src/main/resources/application.properties`

### `Unexpected end of JSON input`
- Usually happens when frontend cannot reach backend API or response is empty
- Ensure frontend Vite proxy is active (`npm run dev` restart after config changes)

### TensorFlow model loading errors
- Ensure model exists at `ai-service/model.h5`
- Use compatible Python/TensorFlow environment
- `ai-service/predict.py` already includes compatibility handling for some Keras config mismatches

## Notes

- `model.h5` is large and should usually stay out of Git history.
- History is stored in MongoDB and also cached in browser for fallback.

## Quick Start (3 terminals)

Terminal 1 (AI service):

```powershell
cd "<project-root>"
python -m uvicorn predict:app --host 127.0.0.1 --port 8000 --app-dir ai-service
```

Terminal 2 (Backend):

```powershell
cd "<project-root>\backend"
.\mvnw.cmd spring-boot:run
```

Terminal 3 (Frontend):

```powershell
cd "<project-root>\frontend"
npm run dev
```

Open: `http://localhost:5173`
