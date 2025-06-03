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

## Installation

1. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Simulation

To run the simulation with default parameters:

```
python run_simulation.py
```

This will:
1. Run the simulation for 100 steps with 100 customers and 50 products
2. Export the data to CSV files in the `../data_source/` directory
3. Generate visualization plots in the `../data_source/` directory

## Customizing the Simulation

You can modify the simulation parameters in `run_simulation.py`:

```python
model = run_simulation(
    num_steps=100,      # Number of simulation steps
    num_customers=100,  # Number of customer agents
    num_products=50     # Number of product agents
)
```

## Output Data

The simulation generates the following CSV files:

- `Walmart_model_data.csv`: Overall model metrics over time
- `Walmart_customers.csv`: Customer agent data
- `Walmart_products.csv`: Product agent data
- `Walmart_transactions.csv`: Transaction records

## Visualization

The simulation generates a visualization file `simulation_results.png` with four plots:
1. Total Sales Over Time
2. Customer Count Over Time
3. Product Count Over Time
4. Distribution of Customer Sales

## Extending the Model

To extend the model, you can:

1. Add new agent types in `walmart_agents.py`
2. Modify agent behaviors in the `step()` methods
3. Add new data collection metrics in `walmart_model.py`
4. Create new visualizations in `run_simulation.py` 