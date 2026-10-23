# Spotter: Weather-Aware Truck Routing Platform

A full-stack intelligent routing platform designed to calculate driving routes for commercial trucks, inspect weather risk conditions (wind gusts, precipitation, snow, visibility) along corridor checkpoints, and rank alternative routes based on safety and efficiency.

---

## Architecture Overview

- **Frontend**: React 18 + TypeScript + Vite + Material UI (MUI) + Leaflet / React-Leaflet
- **Backend**: Python 3.12 + Django 5 + Django REST Framework + django-cors-headers
- **Single Source of Truth**: The backend manages routing integrations, weather risk assessment, checkpoint sampling, and route scoring. The frontend displays maps, route alternatives, and risk alerts.

---

## Directory Structure

```text
spotter-ai/
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main application layout with MUI
│   │   ├── App.test.tsx        # Vitest & React Testing Library tests
│   │   ├── main.tsx            # Vite root entry
│   │   ├── setupTests.ts       # Test setup for Vitest / RTL
│   │   └── vite-env.d.ts       # Vite TypeScript client declarations
│   ├── package.json            # React, MUI, Leaflet, Vitest dependencies
│   ├── tsconfig.json           # Frontend TypeScript configuration
│   └── vite.config.ts          # Vite bundler & Vitest configuration
├── backend/
│   ├── config/                 # Django project settings & root URLs
│   ├── routing/                # Django routing application & API views
│   ├── requirements.txt        # Backend dependencies
│   ├── pytest.ini              # Pytest configuration
│   └── manage.py               # Django management CLI
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # Documentation and run instructions
```

---

## Prerequisites

- **Python**: 3.12+
- **Node.js**: v20+ or v22+
- **npm**: v10+

---

## Local Setup & Running

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Backend Setup & Run

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (if not already created):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations (initial setup):
   ```bash
   python manage.py migrate
   ```
5. Start the Django API server:
   ```bash
   python manage.py runserver 8000
   ```
   The backend API will be available at `http://localhost:8000`.
   Verify the health endpoint:
   ```bash
   curl http://localhost:8000/api/health/
   ```

### 3. Frontend Setup & Run

1. In a separate terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend web application will be accessible at `http://localhost:5173`.

---

## Running Tests

### Backend Tests (pytest)
```bash
cd backend
venv/bin/pytest
```

### Frontend Tests (Vitest)
```bash
cd frontend
npm test
```

### Frontend Build Check
```bash
cd frontend
npm run build
```

### Django System Check
```bash
cd backend
venv/bin/python manage.py check
```
