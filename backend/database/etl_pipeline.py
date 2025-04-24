import os
from method.walmart_model import WalmartModel
from method.run_simulation import run_simulation
from load_to_postgres import main as load_to_db

def run_etl_pipeline():
    try:
        # Step 1: Run ABM simulation
        print("Running ABM simulation...")
        model = run_simulation()
        
        # Step 2: Load to PostgreSQL
        print("Loading data to PostgreSQL...")
        load_to_db()
        
        print("ETL pipeline completed successfully!")
        
    except Exception as e:
        print(f"ETL pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_etl_pipeline()