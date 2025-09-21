# Walmart E-commerce Agent-Based Model

This module contains an agent-based model (ABM) simulation of a Walmart-like e-commerce platform using the Mesa framework.

## Overview

The simulation models:

- Customers with budgets and product preferences
- Products with prices, inventory levels, and categories
- Purchase behaviors and inventory management

## Files

- `walmart_model.py`: Contains the main model class
- `walmart_agents.py`: Contains the Customer and Product agent classes
- `run_simulation.py`: Script to run the simulation and export data
- `requirements.txt`: Dependencies for the simulation
- `helper/`: Helper files from id_tracking to saving files

   ```

## Running the Simulation

To run the simulation with default parameters:

```
python run_simulation.py
```

This will:

1. Run the simulation for 100 steps with 100 customers and 170 products
2. Export the data to CSV files in the `../data_source/agm_output` directory
3. Save agent states for continuation in the `../data_source/agm_agent_save` directory

## Customizing the Simulation

You can modify the simulation parameters in `run_simulation.py`:

```python
model = run_simulation(
  start_date=20250101,  #YYYYMMDD format
  num_steps=100,        # Number of simulation steps
  num_customers=100,    # Number of customer agents
  num_products=50       # Number of product agents
    
)
```

## Output Data

The simulation generates the following CSV files:

- `Walmart_model_data.csv`: Overall model metrics over time
- `Walmart_customers.csv`: Customer agent data
- `Walmart_products.csv`: Product agent data
- `Walmart_transactions.csv`: Transaction records

## Extending the Model

To extend the model, you can:

1. Add new agent types in `walmart_agents.py`
2. Modify agent behaviors in the `step()` methods
3. Add new data collection metrics in `walmart_model.py`

