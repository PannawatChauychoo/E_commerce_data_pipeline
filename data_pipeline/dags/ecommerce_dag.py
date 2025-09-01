# Airflow being run in docker container
from datetime import datetime, timedelta

from airflow import DAG  # type: ignore
from airflow.operators.bash import BashOperator  # type: ignore

# Default arguments for all tasks
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
with DAG(
    dag_id="ecommerce_dag",
    default_args=default_args,
    description="Postgres load → dbt run",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    # 2. Import new data into Postgres
    import_to_postgres = BashOperator(
        task_id="import_to_postgres",
        cwd="/opt/airflow/backend",
        bash_command="python ./database/load_to_postgres.py",
    )

    # 3. Run dbt transformations
    dbt_run = BashOperator(
        task_id="dbt_run",
        cwd="/opt/airflow/dbt",
        bash_command="dev_dbt_run.sh",
    )

    # Define the order of execution
    import_to_postgres >> dbt_run

if __name__ == "__main__":
    dag.test()
