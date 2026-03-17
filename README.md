# Purchase Order Management System (Backend)

FastAPI + SQLAlchemy + PostgreSQL backend for managing Vendors, Products, and Purchase Orders.

## Prerequisites

- Python 3.10+
- PostgreSQL 13+

## Setup

1) Create a database (example):

```sql
CREATE DATABASE po_db;
```

2) Configure environment variables.

Create a `.env` in this folder:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/po_db
```

3) Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4) Run the API:

```bash
uvicorn app.main:app --reload
```

API docs:
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Database / Schema

This project includes **SQL scripts** for submission:

- `db/schema.sql`: fresh schema for PostgreSQL
- `db/migrate_existing.sql`: alters an existing DB created earlier by `create_all()`

### Apply schema (fresh DB)

```bash
psql -U postgres -d po_db -f db/schema.sql
```

### Migrate existing DB

```bash
psql -U postgres -d po_db -f db/migrate_existing.sql
```

## Notes

- During development, tables can still be created on startup, but for assignment submission prefer using `db/schema.sql`.
