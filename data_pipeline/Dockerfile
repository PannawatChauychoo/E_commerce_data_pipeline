FROM apache/airflow:3.0.0-python3.12

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

USER airflow
ADD requirements_airflow.txt .
RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements_airflow.txt
