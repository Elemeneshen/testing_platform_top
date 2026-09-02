# Testing Platform

A web platform for student testing with FastAPI backend and React frontend.

## Structure

- `/backend` - FastAPI application
- `/frontend` - Vite + React + TypeScript application

## Prerequisites

- Python 3.12+
- Node.js 20.19.0+ (or >=22.12.0)
- PostgreSQL 15+
- Docker and Docker Compose (optional, for containerized deployment)

## Backend Setup

1. Navigate to `/backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (copy `.env.example` to `.env` and adjust)
4. Run migrations: `alembic upgrade head`
5. Start the server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

The API will be available at `http://localhost:8000`
Health check: `GET http://localhost:8000/health` returns `{"status": "ok"}`

## Frontend Setup

1. Navigate to `/frontend`
2. Install dependencies: `npm install`
3. Set up environment variables (copy `.env.example` to `.env` and adjust)
4. Start the development server: `npm run dev`

The frontend will be available at `http://localhost:5173`

## Docker Setup

1. Copy `.env.example` to `.env` in the project root and adjust variables if needed
2. Run: `docker compose up -d`
3. Services will be available:
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:5173`
   - PostgreSQL: `localhost:5432`

## Environment Variables

See `.env.example` for required variables:
- `DATABASE_URL` - PostgreSQL connection string (asyncpg driver)
- `JWT_SECRET` - Secret key for JWT signing
- `JWT_ALGORITHM` - Algorithm for JWT (default: HS256)

## Testing

Run backend tests: `cd backend && pytest`

## License

MIT