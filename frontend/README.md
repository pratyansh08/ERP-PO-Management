# Frontend (Vanilla JS + Bootstrap)

This folder contains 2 static pages:

- `dashboard.html`: list Purchase Orders, with a modal to view details
- `create-po.html`: create a Purchase Order with dynamic item rows and live total preview (includes 5% tax)

## How it connects to the backend

All requests use the browser `fetch()` API to call the FastAPI backend.

The base URL is defined in:

- `frontend/assets/api.js` → `API_BASE`

Default:

- `http://127.0.0.1:8000/api`

If your backend runs elsewhere, change `API_BASE` accordingly.

## Run instructions

1) Start the backend:

```bash
cd C:\Users\praty\po-backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2) Serve the frontend with a static server (recommended, avoids `file://` quirks):

```bash
cd C:\Users\praty\po-backend\frontend
python -m http.server 5500
```

3) Open:

- Dashboard: `http://127.0.0.1:5500/dashboard.html`
- Create PO: `http://127.0.0.1:5500/create-po.html`

## Notes

- The backend has CORS enabled for development (`allow_origins=["*"]`) so this static frontend can call it.
