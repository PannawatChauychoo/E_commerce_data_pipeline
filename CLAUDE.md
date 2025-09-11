# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a portfolio project demonstrating an end-to-end e-commerce data pipeline simulation. The project uses Agent-based modeling to generate synthetic customer data and processes it through a modern data engineering stack (PostgreSQL, Airflow, dbt, Django, Next.js).

## Architecture

The project consists of four main components:

### 1. Data Pipeline (`data_pipeline/`)
- **Airflow**: Orchestrates the entire pipeline
- **dbt**: Transforms raw data into analytics-ready tables
- **PostgreSQL**: Primary database with `walmart` schema
- **Method simulation**: Agent-based customer behavior simulation

### 2. Backend (`backend/`)
- **Django REST API**: Provides simulation control and analytics endpoints
- **Database module**: Handles PostgreSQL data loading and operations
- **API module**: REST endpoints for frontend integration

### 3. Frontend (`front_end/`)
- **Next.js**: Interactive dashboard application
- **Tailwind CSS + ShadcnUI**: Styling and components
- **Recharts**: Data visualization
- **PowerBI integration**: Embedded analytics dashboards

### 4. Analytics (`walmart_EDA/`)
- **Jupyter notebooks**: Exploratory data analysis
- **Model definitions**: Customer segmentation and behavior models

## Development Commands

### Python Environment Setup
```bash
# Install dependencies using uv (preferred) or pip
uv sync
# OR
pip install -r requirements.txt
```

### Data Pipeline (Airflow + dbt)
```bash
cd data_pipeline
# Start the full Airflow stack with PostgreSQL
docker-compose up --build

# Access services:
# - Airflow UI: http://localhost:8080 (airflow/airflow)
# - PostgreSQL: localhost:5432
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090

# Run dbt manually inside container
docker-compose exec airflow-worker bash
cd /opt/airflow/dbt
dbt deps
dbt build --full-refresh --target dev
```

### Backend (Django)
```bash
cd backend
# Run Django development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Access Django admin: http://localhost:8000/admin
# API endpoints: http://localhost:8000/api
```

### Frontend (Next.js)
```bash
cd front_end
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build
npm start

# Linting
npm run lint

# Access dashboard: http://localhost:3000
```

### Testing
```bash
# Python tests
pytest

# Run simulation
cd data_pipeline/method
python simulation_runner.py
```

## Key Configuration Files

- **`pyproject.toml`**: Python project dependencies and metadata
- **`data_pipeline/docker-compose.yaml`**: Airflow orchestration setup
- **`data_pipeline/dbt/dbt_project.yml`**: dbt transformation configuration
- **`backend/rest_api/settings.py`**: Django configuration with PostgreSQL connection
- **`front_end/package.json`**: Next.js application dependencies

## Database Schema

The project uses PostgreSQL with a `walmart` schema containing:
- **Raw tables**: Customer, product, and transaction data
- **Staging views**: dbt staging transformations
- **Core tables**: Dimensional models (customers, products, orders)
- **Analytics views**: KPIs (CLV, purchase frequency, segment analysis)

## Data Flow

1. **Simulation**: Agent-based models generate synthetic customer behavior
2. **Ingestion**: Raw data loaded into PostgreSQL via `load_to_postgres.py`
3. **Transformation**: dbt processes raw data into dimensional models
4. **API**: Django serves processed data via REST endpoints
5. **Visualization**: Next.js dashboard displays KPIs and trends

## Environment Variables

Required environment variables (create `.env` files):
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`: PostgreSQL connection
- `AIRFLOW_UID`: User ID for Airflow containers
- Django `SECRET_KEY` and debug settings

## Development Workflow

1. Start PostgreSQL and Airflow: `cd data_pipeline && docker-compose up -d`
2. Run simulation and data load via Airflow DAG
3. Start Django backend: `cd backend && python manage.py runserver`
4. Start Next.js frontend: `cd front_end && npm run dev`
5. Access dashboard at http://localhost:3000

## Important Notes

- The project uses Python 3.13+ with modern dependency management (uv/pip)
- Database connections require the `walmart` schema to exist
- dbt models follow medallion architecture (staging → core → marts)
- Frontend integrates with PowerBI for advanced analytics
- All services are containerized for consistent development environment