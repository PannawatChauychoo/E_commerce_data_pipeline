import argparse
import datetime as dt
import os
from pathlib import Path

import numpy as np
from helper.save_load import load_agents_from_latest_json, save_agents_to_json
from walmart_model import WalmartModel

"""
Run the simulation
- Input: days, number of customers, number of products
- Output: csv files in data_source/agm_output

Edge cases considerations:
- Run daily

"""

# Ignore non-crucial warnings
old_settings = np.seterr(divide="ignore", invalid="ignore")
# np.seterr(**old_settings) -- to restore original warnings

# Always execute at data_pipeline directory
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)


def run_simulation(
    days: int = 1,
    total_customers_num: int = 500,
    cust1_2_ratio: float = 0.5,
    products_num: int = 10,
    run_mode: str = "prod",
):
    """
    Input:
        - days -> steps to simulate
        - total_customers_num
        - cust1_2_ratio -> fraction of cust1 vs cust2
        - products_num -> number of product per categories (default 12 categories)
    """

    print("Initializing Walmart simulation...")

    # Starting the simulation at the latest available date to avoid missing data
    if run_mode.lower() == "prod":
        print("---- Production Mode ----")
        transaction_folder = Path("./data_source/agm_output_test")
    elif run_mode.lower() == "test":
        print("---- Test Mode ----")
        transaction_folder = Path("./data_source/agm_output")
    else:
        return "Invalid mode"

    if not transaction_folder.exists() or not any(transaction_folder.iterdir()):
        Path.mkdir(transaction_folder, parents=True, exist_ok=True)
        latest_date = dt.datetime.now()
    else:
        subfolders = [f for f in transaction_folder.iterdir() if f.is_dir()]
        latest_folder = str(max(subfolders, key=lambda x: str(x).split("=")[-1]))
        latest_date = latest_folder.split("=")[-1]
        today = dt.datetime.now()
        if latest_date == today.strftime("%Y%m%d"):
            run_again = input(
                "Already run for the day. Do you want to run again? (y/n)"
            )
            if run_again.lower() == "y":
                latest_date = today
            elif run_again.lower() == "n":
                return print("See you tomorrow!")
            else:
                return print("Invalid response")
        else:
            latest_date = dt.datetime.strptime(latest_date, "%Y%m%d")

    # Setting up the model
    cust1_n = int(int(total_customers_num) * float(cust1_2_ratio))
    cust2_n = int(total_customers_num) - cust1_n
    model = WalmartModel(
        start_date=latest_date,  # Start from 2 years ago
        max_steps=int(days),
        n_customers1=cust1_n,
        n_customers2=cust2_n,
        n_products_per_category=int(products_num),
        mode=run_mode,
    )

    # Loading past agent state
    loaded_file, loaded_id_dict = load_agents_from_latest_json(
        model, model.class_registry, mode=run_mode
    )
    if loaded_file and loaded_id_dict:
        print(f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}")
    else:
        print("No saved files")

    # Run the simulation
    print("Running simulation...")
    model.initialize_extra_agents()
    model.run_model()

    # Print summary
    print("\nSimulation Summary:")
    print(f"Total days simulated: {model.schedule.steps}")
    print(f"Starting date: {latest_date}")
    print(f"Final date: {model.current_date.strftime('%m/%d/%Y')}")

    # Saving the agent state and result
    saved_file = save_agents_to_json(model, mode=run_mode)
    assert saved_file.exists(), print("Can't find recently saved file")

    df_result_dict = model.save_results_as_df()
    final_paths = model.write_results_csv(df_result_dict)
    for f in final_paths:
        assert f.exists(), print(f"Cannot find file {f}")

    # Get the collected data
    model_data = model.datacollector.get_model_vars_dataframe()
    print(f"Total products sold: {int(model_data['Total Products Sold'].sum())}")
    print(f"Total sales: ${model_data['Total Sales'].sum():.2f}")
    print("\nSimulation completed successfully!")


def main():
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="Run simulation for given days based on given number of customers and products",
    )
    parser.add_argument("days")
    parser.add_argument("customer_num")
    parser.add_argument("customer_ratio")
    parser.add_argument("product_num")
    parser.add_argument("run_mode")

    args = parser.parse_args()
    run_simulation(
        args.days,
        args.customer_num,
        args.customer_ratio,
        args.product_num,
        args.run_mode,
    )


if __name__ == "__main__":
    main()
