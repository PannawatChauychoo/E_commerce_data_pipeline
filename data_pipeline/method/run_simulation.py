from walmart_model import WalmartModel
import pandas as pd
from datetime import datetime
import argparse
from pathlib import Path
"""
Run the simulation
- Input: days, number of customers, number of products
- Output: csv files in data_source/agm_output

Edge cases considerations:
- Run daily
- 

"""


def run_simulation(days=1, customers_num=500, products_num=10):
    # Initialize the model
    print("Initializing Walmart simulation...")
    wd = str(Path(__file__).parent)
    
    transaction_file = wd + '/../data_source/agm_output/transactions.csv'
    cust1_file = wd + '/../data_source/agm_output/cust1_demographics.csv'
    cust2_file = wd + '/../data_source/agm_output/cust2_demographics.csv'
    product_file = wd + '/../data_source/agm_output/products.csv'
    
    #Starting the simulation at the latest available date to avoid missing data
    df = pd.read_csv(transaction_file)
    latest_simulated_date = pd.to_datetime(df['date_purchased']).max()
    if latest_simulated_date == datetime.now():
        return print('Already run for the day')
    
    model = WalmartModel(
        start_date=latest_simulated_date,  # Start from 2 years ago 
        max_steps=days,  
        n_customers=customers_num,
        n_products_per_category=products_num,
    )
    # Run the simulation
    print("Running simulation...")
    model.run_model()
    
    # Export data
    print("Exporting transaction data...")
    model.export_transactions(path=transaction_file)
    model.export_demographics(path1=cust1_file, path2=cust2_file)
    model.export_products(path=product_file) 
    
    # Print summary
    print("\nSimulation Summary:")
    print(f"Total days simulated: {model.schedule.steps}")
    print(f"Starting date: {latest_simulated_date}")
    print(f"Final date: {model.current_date.strftime('%m/%d/%Y')}")
    
    # Load and print transaction counts
    all_transactions = pd.read_csv(transaction_file)
    
    print(f"\nTotal transactions: {len(all_transactions)}")
    
    # Get the collected data
    model_data = model.datacollector.get_model_vars_dataframe()
    print(f"Total products sold: {int(model_data['Total Products Sold'].sum())}")
    print(f"Total sales: ${model_data['Total Sales'].sum():.2f}")
    
    print("\nSimulation completed successfully!")

def main():
    parser = argparse.ArgumentParser(
        prog='ProgramName',
        description='Run simulation for given days based on given number of customers and products'
    )
    parser.add_argument('days')
    parser.add_argument('customer_num')
    parser.add_argument('product_num')

    args = parser.parse_args()
    run_simulation(args.days, args.customer_num, args.product_num)

if __name__ == "__main__":
    main()