import os
import pandas as pd
from walmart_model import WalmartModel
import matplotlib.pyplot as plt

def run_simulation(num_steps=100, num_customers=100, num_products=50):
    """
    Run the Walmart simulation for a specified number of steps.
    
    Args:
        num_steps: Number of simulation steps to run
        num_customers: Number of customer agents
        num_products: Number of product agents
        
    Returns:
        model: The simulation model after running
    """
    # Create and run the model
    model = WalmartModel(num_customers=num_customers, num_products=num_products)
    
    for i in range(num_steps):
        model.step()
        if i % 10 == 0:
            print(f"Step {i}: Total Sales = {model.datacollector.model_vars['Total_Sales'][-1]}")
    
    return model

def export_data(model, output_dir="../data_source"):
    """
    Export simulation data to CSV files.
    
    Args:
        model: The simulation model
        output_dir: Directory to save the CSV files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get model data
    model_data = model.datacollector.get_model_vars_dataframe()
    
    # Get agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()
    
    # Filter agent data by type
    customer_data = agent_data[agent_data['Type'] == 'Customer']
    product_data = agent_data[agent_data['Type'] == 'Product']
    
    # Export to CSV
    model_data.to_csv(f"{output_dir}/Walmart_model_data.csv", index=True)
    customer_data.to_csv(f"{output_dir}/Walmart_customers.csv", index=True)
    product_data.to_csv(f"{output_dir}/Walmart_products.csv", index=True)
    
    # Create transaction data from customer purchase history
    transactions = []
    for agent in model.schedule.agents:
        if agent.type == "Customer" and hasattr(agent, 'purchase_history'):
            for purchase in agent.purchase_history:
                transactions.append({
                    'customer_id': agent.unique_id,
                    'product_id': purchase['product_id'],
                    'quantity': purchase['quantity'],
                    'price': purchase['price'],
                    'total': purchase['total'],
                    'step': purchase['step']
                })
    
    # Export transactions
    if transactions:
        transactions_df = pd.DataFrame(transactions)
        transactions_df.to_csv(f"{output_dir}/Walmart_transactions.csv", index=False)
    
    print(f"Data exported to {output_dir}")

def plot_results(model):
    """
    Plot simulation results.
    
    Args:
        model: The simulation model
    """
    # Get model data
    model_data = model.datacollector.get_model_vars_dataframe()
    
    # Create figure with subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot total sales over time
    axs[0, 0].plot(model_data.index, model_data['Total_Sales'])
    axs[0, 0].set_title('Total Sales Over Time')
    axs[0, 0].set_xlabel('Step')
    axs[0, 0].set_ylabel('Total Sales')
    
    # Plot customer count over time
    axs[0, 1].plot(model_data.index, model_data['Customer_Count'])
    axs[0, 1].set_title('Customer Count Over Time')
    axs[0, 1].set_xlabel('Step')
    axs[0, 1].set_ylabel('Count')
    
    # Plot product count over time
    axs[1, 0].plot(model_data.index, model_data['Product_Count'])
    axs[1, 0].set_title('Product Count Over Time')
    axs[1, 0].set_xlabel('Step')
    axs[1, 0].set_ylabel('Count')
    
    # Plot sales per customer
    axs[1, 1].hist([agent.sales for agent in model.schedule.agents if agent.type == "Customer"], bins=20)
    axs[1, 1].set_title('Distribution of Customer Sales')
    axs[1, 1].set_xlabel('Sales')
    axs[1, 1].set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig("../data_source/simulation_results.png")
    plt.close()

if __name__ == "__main__":
    # Run simulation
    model = run_simulation(num_steps=100, num_customers=100, num_products=50)
    
    # Export data
    export_data(model)
    
    # Plot results
    plot_results(model)
    
    print("Simulation completed successfully!") 