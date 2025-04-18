from walmart_model import WalmartModel
import pandas as pd
from datetime import datetime

def run_simulation():
    # Initialize the model
    print("Initializing Walmart simulation...")
    model = WalmartModel(
        start_date=datetime.now().strftime('%m/%d/%Y'),  # Start from today
        max_steps=15,  # Run for 100 days
        n_customers=500,
        n_products_per_category=10,

    )
    
    # Run the simulation
    print("Running simulation...")
    model.run_model()
    
    # Export transactions
    print("Exporting transaction data...")
    model.export_transactions()
    
    # Print summary
    print("\nSimulation Summary:")
    print(f"Total days simulated: {model.schedule.steps}")
    print(f"Final date: {model.current_date.strftime('%m/%d/%Y')}")
    
    # Load and print transaction counts
    cust1_transactions = pd.read_csv('/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/cust1_transactions.csv')
    cust2_transactions = pd.read_csv('/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/cust2_transactions.csv')
    
    print(f"\nTotal Cust1 transactions: {len(cust1_transactions)}")
    print(f"Total Cust2 transactions: {len(cust2_transactions)}")
    
    # Get the collected data
    model_data = model.datacollector.get_model_vars_dataframe()
    print(f"Total products sold: {int(model_data['Total Products Sold'].sum())}")
    print(f"Total sales: ${model_data['Total Sales'].sum():.2f}")
    
    print("\nSimulation completed successfully!")

if __name__ == "__main__":
    run_simulation() 