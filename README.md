# Spotter: Weather-Aware Truck Routing Platform

A full-stack intelligent routing platform designed to calculate driving routes for commercial trucks, inspect weather risk conditions (wind gusts, precipitation, snow, visibility) along corridor checkpoints, and rank alternative routes based on safety and efficiency.

---

## Architecture Note & Design Principles

### 1. Single Source of Truth
- The **backend (Django REST Framework)** is the sole authority for:
  - Driving corridor generation & coordinate geometries (up to 3 routes)
  - Corridor checkpoint sampling (at 10, 25, or 50-mile intervals)
  - ETA propagation per checkpoint
  - Weather forecast retrieval (Open-Meteo) & explicit data availability handling
  - Weather hazard risk scoring (wind, rain, snow)
  - Truck weight & load-adjusted risk modifiers (e.g., rollover risk on light loads in high winds)
  - Final route eligibility and safety ranking
- The **frontend (React + TypeScript + MUI + Leaflet)** consumes backend responses purely for visualization (interactive map rendering, checkpoint inspection, risk heatmaps, and recommendation badges). **The frontend never duplicates routing or safety decision logic.**

### 2. Routing Provider Strategy: OpenRouteService & Alternative Corridors
- **Primary Provider**: OpenRouteService (ORS) with the dedicated commercial truck profile (`driving-hgv`).
- **Authorization & Security**: Server-side API key authentication using the `Authorization: <api_key>` header. Keys and credential headers are never logged or exposed in query URLs.
- **Short Trips (< 90 km)**: Requests native ORS alternative routes (`alternative_routes: { target_count: 3, share_factor: 0.6, weight_factor: 1.4 }`).
- **Long Trips (>= 90 km / 300+ miles) & Error 2004 Fallback**:
  - OpenRouteService public API imposes a 100 km distance cap on native `alternative_routes` (returning error `2004`).
  - When the trip distance is $\ge 90$ km, or if ORS returns error `2004`, the backend automatically falls back to **lateral via-waypoint corridor derivation**.
  - **Important Distinction**: Via-waypoint alternatives represent **"alternative corridors"** derived by sampling perpendicular offset waypoints across the route corridor, rather than native provider alternatives.
- **Via-Waypoint Offset Scaling**: Offset distance is dynamically scaled with trip length (`trip_distance_km * 0.08`), clamped between `MIN_LATERAL_OFFSET_KM = 20.0` km and `MAX_LATERAL_OFFSET_KM = 80.0` km.
- **Detour Sanity Filter**: Candidates with distance or duration exceeding `1.5x` of the primary route are rejected (`MAX_DETOUR_RATIO = 1.5`).
- **Overlap Deduplication Filter**: Candidates sharing more than `80%` of their length with any previously accepted route are rejected (`MAX_OVERLAP_SHARE_RATIO = 0.80`).
- **Snapping Resilience**: If a via-waypoint lands where no road can be snapped (ORS error `2010`), the candidate is skipped gracefully without failing the request.
- **Quota Cap**: Extra candidate routing calls are capped at a maximum of 4 calls per request. Geocoding queries are cached locally for 7 days.
- **Vehicle Weight vs Dimensions**: The request payload includes `load_weight_lb` (cargo payload weight). Because physical vehicle dimensions (height, width, axle count) are not collected, artificial dimension caps are not passed to ORS to avoid unintended routing failures. `load_weight_lb` is reserved for backend weather risk calculations (crosswind rollover vulnerability).

### 2. Main Analysis API Contract: `POST /api/routes/analyze/`
- **Throttling**: Enforced via DRF `ScopedRateThrottle` (`route_analysis: 30/minute`) to preserve external provider quotas and prevent denial-of-service.
- **Error Handling**: Standardized error envelope on all 4xx/5xx responses:
  ```json
  {
    "error": {
      "code": "validation_error | request_throttled | api_error",
      "message": "Human-readable summary message.",
      "details": {
        "field_name": ["Specific validation message"]
      }
    }
  }
  ```

#### Request Schema
| Field | Type | Description / Constraints |
| :--- | :--- | :--- |
| `origin` | `string` | Origin address or coordinates (non-empty) |
| `destination` | `string` | Destination address or coordinates (non-empty) |
| `departure_time` | `string` (ISO 8601) | **Must include timezone offset** (e.g. `2026-10-23T14:00:00Z`). Naive timestamps are strictly rejected. |
| `load_weight_lb` | `number` | Positive gross truck/cargo weight in pounds (`> 0`) |
| `checkpoint_interval_miles` | `number` | Sampling spacing along route corridor: `10`, `25`, or `50` |

#### Response Schema Structure
- `routes_requested`: `number` (target 3)
- `routes_returned`: `number`
- `fewer_routes_reason`: `string | null` (populated when `< 3` corridors exist or provider limits return fewer)
- `routes`: Array of route alternatives:
  - `route_id`, `provider_summary`, `geometry` (ordered `[lat, lon]` pairs), `distance_miles`, `duration_minutes`
  - `checkpoints`: Sampled points along the route corridor:
    - `checkpoint_id`, `lat`, `lon`, `cumulative_distance_miles`
    - `eta`: ISO 8601 timestamp with timezone offset
    - `forecast_timestamp`: Matching forecast hour timestamp
    - `weather`: Values with explicit availability:
      - `wind_speed_mph`, `wind_speed_availability` (`available | unavailable | missing`)
      - `rain_in_per_hr`, `rain_availability` (`available | unavailable | missing`)
      - `snow_in_per_hr`, `snow_availability` (`available | unavailable | missing`)
    - `condition_risks`: Per-condition risks (`wind_risk`, `rain_risk`, `snow_risk`)
    - `weather_risk`: Base risk level (`low | moderate | high | severe | no_travel | unknown`)
    - `load_adjusted_risk`: Weight-factored risk level
    - `load_rule_applied`: Rule description (e.g., "High-profile light-load wind penalty applied")
  - `metrics`:
    - `miles_per_risk_category`: Dict mapping each risk level to cumulative miles
    - `severe_miles`, `high_miles`, `no_travel_miles`, `unknown_miles`
    - `average_risk`: Overall route risk tier
    - `has_no_travel_segment`: Boolean flag
    - `forecast_coverage_pct`: Percentage of route covered by active forecasts (0-100)
  - `eligibility`: `is_eligible` (`boolean`) and `ineligibility_reasons` (`string[]`)
- `recommendation`:
  - `recommended_route_id`: Selected safest route ID (or `null`)
  - `route_eligibility`: Map of route ID to boolean eligibility
  - `ranking_reasons`: Array of human-readable rationale
  - `no_route_meets_safety_thresholds`: Boolean indicator when all alternatives fail safety rules
- `forecast_timeline`: Array of 48-hour forward timelines per checkpoint (placeholder for Task 10A)
- `warnings`: Operational and degraded condition warnings
- `provider_errors`: Upstream provider error objects `{ provider, code, message }`

---

## Directory Structure

```text
spotter-ai/
├── frontend/
│   ├── src/
│   │   ├── types/
│   │   │   ├── api.ts          # Typed API contracts matching backend DRF serializers
│   │   │   └── api.test.ts     # Schema typing and contract validation tests
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
│   ├── routing/
│   │   ├── serializers.py      # DRF request and response validation serializers
│   │   ├── views.py            # HealthCheckView and RouteAnalyzeView
│   │   ├── urls.py             # Route definitions
│   │   ├── exceptions.py       # Standardized exception handler & error envelope
│   │   └── tests/
│   │       ├── test_health.py  # Health endpoint tests
│   │       └── test_route_analyze_schema.py # Schema, validation & throttling tests
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
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the Django API server:
   ```bash
   python manage.py runserver 8000
   ```
   The backend API will be available at `http://localhost:8000`.
   - Health endpoint: `GET http://localhost:8000/api/health/`
   - Route Analysis endpoint: `POST http://localhost:8000/api/routes/analyze/`

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

---

## Manual Testing with Live OpenRouteService API Key (300+ Mile Route)

To test live commercial truck routing on a 300+ mile cross-country route (e.g., Denver, CO to Salt Lake City, UT ~ 504 miles):

### 1. Set Your API Key
In `.env` (or exported in your terminal session):
```bash
export OPENROUTESERVICE_API_KEY="your_openrouteservice_api_key_here"
```

### 2. Start the Backend API Server
```bash
cd backend
source venv/bin/activate
python manage.py runserver 8000
```

### 3. Send the Analysis Request via cURL
```bash
curl -X POST http://localhost:8000/api/routes/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Denver, CO",
    "destination": "Salt Lake City, UT",
    "departure_time": "2026-10-23T14:00:00Z",
    "load_weight_lb": 42000,
    "checkpoint_interval_miles": 25
  }'
```

### 4. What Output to Expect
- **Status**: `HTTP 200 OK`
- **Corridors**: `routes_returned: 2` or `3` distinct driving paths.
- **Primary Route (`route_primary`)**: Direct commercial truck corridor (~504 miles, ~480–520 minutes) along the primary interstate with full `[lat, lon]` geometry.
- **Alternative Corridors (`route_alt_1`, `route_alt_2`)**: Distinct regional bypass corridors derived from scaled lateral via-waypoints that deviate significantly ($> 20$ km offset, $< 80\%$ length overlap).
- **Warnings**: Indicates that alternative corridors were derived via lateral bypasses for long-distance driving.
- **Recommendation**: Designates `route_primary` as the initial baseline with safety ranking rationale.

### 5. Automated Live Integration Test
You can also run the live integration test at any time by supplying your key:
```bash
cd backend
RUN_LIVE_ORS_TESTS=1 OPENROUTESERVICE_API_KEY="your_actual_key" venv/bin/pytest routing/tests/test_live_integration.py
```
