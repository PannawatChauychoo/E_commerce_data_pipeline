# Walmart E-commerce Simulation Project

## 1. Overview

This project simulates a simplified Walmart-like E-commerce platform from end-to-end:

- Generate synthetic purchase data using a Python-based Agent-Based Model (ABM).
- Ingest and store that data in a Postgres database, which runs on a separate machine in a Docker container, connected via Tailscale.
- Transform and load data within Postgres using dbt.
- Visualize the data pipelien and dashboard in a React/Next.js frontend.
- Use Airflow to orchestrate the entire pipeline at a daily interval.

Initial techstack is:
- Frontend: Javascript, React, tailwind, Next.js, Lucid icon
- Testing: Jest
- Backend: NodeJS, Python, dbt
- Database: Postgresql
- Orchestration: airflow

## 2. Goals and Objectives

- Demonstrate a full data pipeline for an E-commerce simulation: Simulation → Remote Postgres → ETL → Visualization.
- Provide a realistic environment reflecting operational constraints: scheduled data ingestion, near real-time reporting, distributed architecture.
- Enable advanced analysis on transactional data (forecasting, recommendations, or monitoring).
- Maintain a well-documented, testable, and modular codebase that other developers can easily contribute to.

## 3. Functional Requirements

### 3.1 Agent-Based Model (ABM)
**Requirement**: Generate synthetic transaction data that mimics real-world purchase patterns.

**Details**:
- Configurable parameters: e.g., number of customers, purchase frequency, product preferences.
- Write data to CSV in data_source/ or insert directly into Postgres (over Tailscale).

### 3.2 Data Ingestion & Remote Postgres (Node.js + Tailscale)
**Requirement**: Provide backend APIs that persist and retrieve data from a Dockerized Postgres database running on another machine.

**Details**:
- Postgres does not run locally or in the same docker-compose.yml.
- Tailscale is used to securely connect to the remote machine that hosts the Postgres container.
- Use environment variables in Node.js (e.g., DB_HOST, DB_PORT, DB_USER, DB_PASSWORD) to connect over Tailscale.
- Provide REST endpoints (e.g., GET /products, POST /orders) and map them to the Postgres schema.

### 3.3 Data Pipeline (Airflow)
**Requirement**: Automate extraction, transformation, and loading of data into a warehouse (Clickhouse/Snowflake).

**Details**:
- Create Airflow DAGs that read from the remote Postgres DB via Tailscale.
- Perform necessary data cleaning or transformations.
- Load final data into the warehouse environment.
- Schedule DAG to run (e.g., every 15 minutes).

### 3.3.1 Data Transformation with dbt
**Requirement**: Transform raw data into analytics-ready tables within PostgreSQL using dbt.

**Details**:
- Set up dbt project structure with models representing business entities and metrics.
- Create staging models that clean and prepare raw data from source tables.
- Develop intermediate models that join and transform staging data.
- Build mart/reporting models that represent final analytics tables for dashboards.
- Implement dbt tests to ensure data quality and integrity.
- Run dbt models through Airflow orchestration.

**dbt Project Structure**:
```
dbt_walmart/
├── models/
│   ├── staging/              # Clean raw data
│   │   ├── stg_customers.sql
│   │   ├── stg_products.sql
│   │   ├── stg_transactions.sql
│   │   └── sources.yml       # Source definitions
│   ├── intermediate/         # Join and transform
│   │   ├── int_customer_transactions.sql
│   │   ├── int_product_sales.sql
│   │   └── int_daily_sales.sql
│   └── marts/                # Business-specific models
│       ├── sales/
│       │   ├── daily_sales_by_product.sql
│       │   ├── monthly_sales_by_category.sql
│       │   └── customer_lifetime_value.sql
│       └── inventory/
│           ├── product_inventory_levels.sql
│           └── restock_recommendations.sql
├── tests/                    # Custom data tests
│   └── validate_sales_totals.sql
├── snapshots/                # Track historical changes
│   └── product_price_history.sql
├── macros/                   # Reusable SQL snippets
│   ├── date_spine.sql
│   └── calculate_revenue.sql
├── dbt_project.yml           # Project configuration
└── profiles.yml              # Connection profiles
```

### 3.4 Frontend (React/Next.js)
**Requirement**: Provide web pages to visualize aggregated metrics, transactions, and system monitoring info.
**Design**:
First page: 
- show the data pipeline with icons from lucid
- AGM simulation data source -> Postgresql -> ETL with DBT -> Analytics -> Dashboard/Forecasting/Recommendation engine
Second page: 
- Dashboard with sidebar on the left with 3 choices:
    - Dashboard - show the aggregated metrics and graphs like trend of purchases over time
    - Transactions - table view of incoming transactions
    - Monitoring - some logging from Airflow
Third page:
-  Documentation
    - Write rationale for each architectural decision in markdown format

**Details**:
- Use React or Next.js with Tailwind CSS for styling.
- Fetch data from the Node.js backend (which is connected to the remote DB).


### 3.5 Testing & Quality Assurance
**Requirement**: Automated testing across the ABM, Node.js backend, and React UI.

**Details**:
- Python: pytest or unittest for verifying ABM behavior (e.g., data output correctness).
- Node.js: Jest (or Mocha + Chai) + supertest for API tests.
- React: Jest for component tests; optionally React Testing Library or Cypress for integration/E2E.
- dbt: Implement schema tests, data tests, and documentation tests.

### 3.6 Documentation
**Requirement**: Comprehensive project documentation.

**Details**:
- A top-level README.md describing how to install, run, and test each component.
- Additional instructions or advanced notes in instructions/ or the documentation section of the frontend.
- Emphasize Tailscale setup steps (i.e., ensuring the Node.js and Airflow containers can reach the remote DB host).
- Document dbt models and transformations with dbt docs.

## 4. Non-Functional Requirements

- **Performance**: Should handle ~1,000,000 synthetic transactions without significant overhead.
- **Scalability**: Architecture that easily adapts to larger datasets or more frequent ingestion.
- **Security**: Basic best practices (no raw credentials in code), Tailscale for secure remote DB access.
- **Maintainability**: Clear separation of concerns, tested code, strong documentation.

## 5. Proposed File Structure

Below is the recommended file layout. Note that we do not define a local Postgres container in our Docker Compose, because Postgres runs on a separate remote machine over Tailscale.

```
WALMART_SIM
├── README.md                   # High-level project overview & setup instructions
├── .gitignore                  # Ignore node_modules, venv, build artifacts, etc.
│
├── instructions/               # Contains instructions.md (existing doc)
│   └── instructions.md
│
├── walmart_EDA/                # (Keep as-is) EDA scripts & data 
│   ├── Data
│   ├── Documentation
│   ├── EDA_scripts
│   └── Model
│
├── data_source/                # Source for CSV output (synthetic or real)
│   ├── Walmart_commerce.csv
│   ├── Walmart_cust.csv
│   ├── Walmart_products.csv
│   └── Walmart_transactions.csv
│
├── data_pipeline/              # Airflow setup & DAGs
│   ├── docker-compose.yml      # For Airflow (no local Postgres needed here)
│   ├── dags/                   # Airflow DAG definitions
│   │   └── dbt_dag.py          # DAG to orchestrate dbt runs
│   ├── requirements.txt        # Python deps for Airflow tasks
│   └── plugins/                # Custom Airflow plugins
│
├── dbt_walmart/                # dbt project for data transformations
│   ├── models/                 # SQL transformation models
│   ├── tests/                  # Data quality tests
│   ├── macros/                 # Reusable SQL functions
│   ├── snapshots/              # Historical data tracking
│   ├── dbt_project.yml         # Project configuration
│   └── profiles.yml            # Connection profiles
│
├── backend/                    # Node.js APIs
│   ├── package.json            # Node dependencies
│   ├── src/                    # Express routes, controllers, DB connection
│   └── tests/                  # Jest or Mocha/Chai test files
│
├── front_end/                  # React or Next.js app
│   ├── package.json            # Frontend dependencies
│   ├── tsconfig.json           # If using TypeScript
│   ├── postcss.config.mjs
│   ├── public/
│   ├── app/                    # React/Next.js pages, components
│   └── tests/                  # Frontend Jest tests
│
└── method/                     # Python-based ABM
    └── purchase_simulator.py   # Example script generating CSV → data_source
```

## 6. Documentation

### Database Connection
Example code to connect with postgresql through tailscale:
```
psql -h 100.97.140.87 -U Pan -d ecommerce_cloud
```

### dbt Implementation

#### Setting Up dbt with PostgreSQL

1. **Install dbt-postgres**:
   ```bash
   pip install dbt-postgres
   ```

2. **Initialize a dbt project**:
   ```bash
   dbt init dbt_walmart
   ```

3. **Configure profiles.yml**:
   ```yaml
   walmart:
     target: dev
     outputs:
       dev:
         type: postgres
         host: 100.97.140.87  # Tailscale IP for remote Postgres
         user: Pan
         password: "{{ env_var('DBT_PASSWORD') }}"  # Use environment variable
         port: 5432
         dbname: ecommerce_cloud
         schema: analytics
         threads: 4
   ```

4. **Create source definition in models/staging/sources.yml**:
   ```yaml
   version: 2

   sources:
     - name: raw
       database: ecommerce_cloud 
       schema: public
       tables:
         - name: customers
         - name: products
         - name: transactions
   ```

#### Example dbt Models

1. **Staging Model (models/staging/stg_transactions.sql)**:
   ```sql
   {{ config(materialized='view') }}

   SELECT
     transaction_id,
     customer_id,
     transaction_date,
     CAST(transaction_timestamp AS timestamp) AS transaction_timestamp,
     CAST(total_amount AS numeric) AS total_amount,
     payment_method,
     store_id
   FROM {{ source('raw', 'transactions') }}
   WHERE transaction_id IS NOT NULL
   ```

2. **Intermediate Model (models/intermediate/int_daily_sales.sql)**:
   ```sql
   {{ config(materialized='table') }}

   SELECT
     DATE_TRUNC('day', transaction_timestamp) AS sale_date,
     SUM(total_amount) AS daily_revenue,
     COUNT(DISTINCT transaction_id) AS transaction_count,
     COUNT(DISTINCT customer_id) AS unique_customers
   FROM {{ ref('stg_transactions') }}
   GROUP BY DATE_TRUNC('day', transaction_timestamp)
   ```

3. **Mart Model (models/marts/sales/monthly_sales_by_category.sql)**:
   ```sql
   {{ config(materialized='table') }}

   SELECT
     DATE_TRUNC('month', t.transaction_timestamp) AS month,
     p.category,
     SUM(i.quantity) AS units_sold,
     SUM(i.quantity * i.unit_price) AS revenue,
     COUNT(DISTINCT t.transaction_id) AS order_count,
     COUNT(DISTINCT t.customer_id) AS customer_count
   FROM {{ ref('stg_transactions') }} t
   JOIN {{ ref('stg_transaction_items') }} i ON t.transaction_id = i.transaction_id
   JOIN {{ ref('stg_products') }} p ON i.product_id = p.product_id
   GROUP BY DATE_TRUNC('month', t.transaction_timestamp), p.category
   ORDER BY month, revenue DESC
   ```

5. **Data Test (tests/validate_sales_totals.sql)**:
   ```sql
   -- This test ensures that transaction line items sum up correctly
   
   WITH transaction_totals AS (
     SELECT
       t.transaction_id,
       t.total_amount AS reported_total,
       SUM(i.quantity * i.unit_price) AS calculated_total
     FROM {{ ref('stg_transactions') }} t
     JOIN {{ ref('stg_transaction_items') }} i ON t.transaction_id = i.transaction_id
     GROUP BY t.transaction_id, t.total_amount
   )
   
   SELECT *
   FROM transaction_totals
   WHERE ABS(reported_total - calculated_total) > 0.01  -- Allow for small rounding differences
   ```

#### Integrating dbt with Airflow

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': 300,  # seconds
}

with DAG(
    dag_id='walmart_dbt_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:

    # Run dbt models in order: staging -> intermediate -> marts
    dbt_run_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command='cd /opt/airflow/dbt_walmart && dbt run --models staging',
        env={'DBT_PROFILES_DIR': '/opt/airflow/dbt_walmart'}
    )

    dbt_run_intermediate = BashOperator(
        task_id='dbt_run_intermediate',
        bash_command='cd /opt/airflow/dbt_walmart && dbt run --models intermediate',
        env={'DBT_PROFILES_DIR': '/opt/airflow/dbt_walmart'}
    )

    dbt_run_marts = BashOperator(
        task_id='dbt_run_marts',
        bash_command='cd /opt/airflow/dbt_walmart && dbt run --models marts',
        env={'DBT_PROFILES_DIR': '/opt/airflow/dbt_walmart'}
    )

    # Run dbt tests after models are built
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt_walmart && dbt test',
        env={'DBT_PROFILES_DIR': '/opt/airflow/dbt_walmart'}
    )

    # Generate dbt documentation
    dbt_docs_generate = BashOperator(
        task_id='dbt_docs_generate',
        bash_command='cd /opt/airflow/dbt_walmart && dbt docs generate',
        env={'DBT_PROFILES_DIR': '/opt/airflow/dbt_walmart'}
    )

    # Define task dependencies
    dbt_run_staging >> dbt_run_intermediate >> dbt_run_marts >> dbt_test >> dbt_docs_generate
```

### Airflow snippet for basic data pipeline
```python
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def extract_data(**kwargs):
    # Placeholder: logic to extract data from a source
    print("Extracting data...")

def transform_data(**kwargs):
    # Placeholder: logic to transform the extracted data
    print("Transforming data...")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': 300,  # seconds
}

with DAG(
    dag_id='simple_data_pipeline',
    default_args=default_args,
    schedule_interval='@daily',    # or a CRON expression
    catchup=False
) as dag:

    task1 = PythonOperator(
        task_id='extract_task',
        python_callable=extract_data
    )

    task2 = PythonOperator(
        task_id='transform_task',
        python_callable=transform_data
    )

    # Orchestrate tasks
    task1 >> task2
```

#### Documentation
**As a Developer**, I want a clear README explaining how to set up Tailscale and point services to the remote DB, so that I can replicate the environment with minimal confusion.

**Acceptance Criteria**:
- README includes Tailscale install steps, environment variables, and tested IP references.
- Key commands for starting the Node.js, React, and Airflow components are documented.

## 7. Technical Stack & Dependencies

- **ABM**: Python (Mesa optional), in method/purchase_simulator.py.
- **Backend**: Node.js with Express (or Fastify), connecting to remote Postgres over Tailscale.
- **Database**: Dockerized Postgres on another machine (no local container).
- **Data Pipeline**: Apache Airflow in Docker Compose, referencing the remote DB.
- **Data Transformation**: dbt (data build tool) for transforming data within PostgreSQL.
- **Data Warehouse**: Clickhouse or Snowflake for final analytics tables.
- **Frontend**: React or Next.js, using Tailwind CSS for styling.
- **Testing**:
  - Python → pytest or unittest.
  - Node.js → Jest + supertest.
  - React → Jest or React Testing Library.
  - dbt → Schema tests and data tests.

## 8. Risks and Mitigations

- **Risk**: Tailscale connectivity or firewall issues might block the remote Postgres connection.
  - **Mitigation**: Ensure all endpoints are properly configured (UDP ports open, stable Tailscale network).
- **Risk**: Large data volumes could degrade performance if the remote Postgres has limited bandwidth.
  - **Mitigation**: Use partial/smaller test datasets; scale Tailscale or network resources as needed.
- **Risk**: dbt transformations might be resource-intensive on the PostgreSQL server.
  - **Mitigation**: Schedule dbt runs during off-peak hours and optimize query performance.
- **Assumption**: Team members have basic Docker and Tailscale knowledge to manage the remote container.