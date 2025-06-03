FROM apache/airflow:3.0.0-python3.12
ADD requirements_airflow.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install --no-cache-dir mesa==2.1.1
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements_airflow.txt
