# Description
This project simulates a simplified Walmart-like E-commerce platform from start to finish. It demonstrates how to:

1. Generate purchase data using an agent-based model (ABM) based on a csv file containing real user transactions
2. Ingest and store that data in Postgres via a Node.js backend,
3. Transform and load the data into Snowflake using Airflow,
4. Visualize the results with a React frontend,
5. Optionally emulate GCP services locally to showcase a cloud-based architecture.


Initial techstack is:
- Frontend: Javascript, React, tailwind, Next.js
- Testing: Jest
- Backend: NodeJS, Python
- Database: Postgres
- Data warehouse: Snowflake
- Data engineer: ETL, airflow
- Cloud: GCP emulator


## Features 
Agent-Based Simulation
Python-based simulator (ABM) that mimics real customer purchase behaviors.
Configurable parameters (e.g., number of customers, purchase frequency, product preferences).
Backend & Database
Node.js backend (Express/Fastify) exposing APIs for product info and order data.
Postgres database storing customer, product, and order records.
Database schema with core tables like customers, products, orders, and order_items.
Frontend (React)
Single-page application for browsing products, viewing cart/order history, and admin metrics.
Integration tests using Jest (and optionally React Testing Library).
Data Pipeline & Orchestration
Airflow DAGs to automate data extraction from Postgres, transform it, and load into Snowflake.
Scheduling to simulate real-time or periodic ingestion of new data.
Data Warehouse (Snowflake)
Mirrors key tables from Postgres (or uses a dimensional model).
Loads data via Airflow tasks (e.g., COPY INTO or SnowflakeOperator).
Cloud Emulator (GCP)
Pub/Sub or Storage emulator to simulate streaming or file staging in a cloud environment.
Local testing without incurring cloud costs.
Testing & CI/CD
Unit tests for backend APIs, frontend components, and Python scripts.
CI pipeline (GitHub Actions/GitLab CI) to run tests on every commit.

### Doc
Project Setup
Create a new directory (e.g., WALMART_SIMULATION) and initialize a Git repository.
Set up a virtual environment (python -m venv venv) for Python-based tasks and ensure it’s in .gitignore.
Include separate folders for backend/, frontend/, data_pipeline/, and agent_based_model/.
Agent-Based Model
In agent_based_model/, create a Python script (e.g., purchase_simulator.py) that spawns multiple “customer agents”.
Each agent simulates behavior such as purchase frequency, product preference, etc.
Output data to either CSV or directly insert records into Postgres.
Database (Postgres) + Node.js Backend
Install and configure Postgres locally (or run via Docker).
Create the E-commerce schema (tables: customers, products, orders, order_items).
In backend/, initialize a Node.js project (npm init) and install a web framework (Express or Fastify).
Implement APIs for retrieving and inserting data (e.g., GET /products, POST /orders).
Connect to Postgres using a Node ORM or query builder (e.g., pg, sequelize, knex).
React Frontend
In frontend/, initialize a React project (using create-react-app or Vite).
Build pages/components for product listings, shopping cart, etc.
Fetch data from your Node.js backend.
Write Jest tests for core components.
Airflow & Data Pipeline
In data_pipeline/, set up an Airflow Docker Compose file or local installation.
Create a DAG that:
Extracts new transaction data from Postgres (or uses a staging CSV).
Transforms data (e.g., cleaning or formatting).
Loads data into Snowflake.
Test your pipeline manually and schedule it to run at intervals (e.g., every 15 minutes).
Snowflake Integration
Sign up for a Snowflake trial or configure local variables if you can’t connect yet.
Create a Snowflake warehouse and database schema for your analytics tables.
Use Airflow to push data from your local environment to Snowflake (e.g., staging files in a GCP emulator bucket, then executing COPY INTO).
GCP Emulator (Optional)
Install and run the Pub/Sub or Storage emulator locally.
Update your Python or Node.js code to publish data (e.g., streaming events) to the emulator.
Consume events via Airflow or a Node subscriber.
Testing & CI/CD
Python: Use pytest or unittest for agent-based simulation tests.
Node.js: Use Jest or Mocha/Chai plus a library like supertest for API tests.
React: Continue to expand Jest tests with coverage for major components.
CI Setup: Implement GitHub Actions or another CI tool to automatically run tests on push or PR.
Documentation & Final Touches
Write a clear README.md explaining how to install, run, and test each part of the project.
Optionally add a quickstart script or Docker Compose that spins everything up (backend, frontend, Postgres, Airflow).
If desired, add a small analytics dashboard (Looker Studio, Tableau, or custom React page) connecting to Snowflake for reporting.


#### Current file structure
WALMART_SIM/                   # Root folder
├─ .git/                       # Git repo goes here
├─ .gitignore                  # Make sure to ignore virtualenv + node_modules + build artifacts
├─ README.md
├─ pyvenv.cfg                  # Belongs to the local virtualenv, typically ignored
├─ Walmart/                    # EDA virtualenv folder for analyzing user behaviors (ignored by Git)
├─ frontend/
│   ├─ package.json
│   ├─ src/
│   ├─ public/
│   ├─ tests/
│   └─ ...
├─ backend/
│   ├─ package.json
│   ├─ src/
│   ├─ tests/
│   └─ ...
├─ methods
│   └─agent_based_model/       
│       └─ ...
└─ data_pipeline/              # Airflow, DAGs, etc.
    └─ ...

