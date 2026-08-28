# A3: Containerized FastAPI Stack with PostgreSQL

Fully containerized multi-container stack with FastAPI and PostgreSQL using Docker Compose.

## Architecture & Storage Layer
- **Layering Proof**: Routes and HTTP validation remain unchanged from A1/A2. The storage engine was replaced with a PostgreSQL repository using `psycopg2`.
- **Persistence**: Managed via named Docker volume `pgdata` mapped to `/var/lib/postgresql/data`.

## How to Run

1. Build and run both containers:
   ```bash
   docker compose up --build