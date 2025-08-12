import argparse
import datetime as dt
import os
from pathlib import Path

import numpy as np
from helper.datetime_conversion import dt_to_str, str_to_dt
from helper.save_load import load_agents_from_newest, save_agents
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


def valid_yyyymmdd(date_str):
    """
    Setting the datetime type for user input
    """
    try:
        str_to_dt(date_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. Use YYYYMMDD."
        )
    return date_str


def run_simulation(
    days: int,
    total_customers_num: int,
    cust1_2_ratio: float,
    start_date: str = "Empty",
    products_num: int = 10,
):
    """
    Input:
        - days -> steps to simulate
        - total_customers_num
        - cust1_2_ratio -> fraction of cust1 vs cust2
        - start_date -> date in YYYYMMDD format
        - products_num -> number of product per categories (default 12 categories)
    """

    print("Initializing Walmart simulation...")
    start = dt.datetime.now()

    run_mode = "Prod"
    if run_mode.lower() == "prod":
        print("---- Production Mode ----")
        transaction_folder = Path("./data_source/agm_output_test")
    elif run_mode.lower() == "test":
        print("---- Test Mode ----")
        transaction_folder = Path("./data_source/agm_output")
    else:
        return "Invalid mode"

    # Setting the start date: if first run, now or start_date input | second+ run, latest simulated date
    if not transaction_folder.exists() or not any(transaction_folder.iterdir()):
        Path.mkdir(transaction_folder, parents=True, exist_ok=True)
        if start_date != "Empty":
            print(f"Starting from {start_date}")
            latest_date = str_to_dt(start_date)
        else:
            print("Starting from today!")
            latest_date = dt.datetime.now()
    else:
        # Problem is the simulated date and the date on the folder is different
        # Fix:
        subfolders = [f for f in transaction_folder.iterdir() if f.is_dir()]
        latest_folder = str(max(subfolders, key=lambda x: str(x).split("=")[-1]))
        latest_date = latest_folder.split("=")[-1]
        today = dt.datetime.now()
        if latest_date == dt_to_str(today):
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
            latest_date = str_to_dt(latest_date)

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
    loaded_file, loaded_id_dict, metadata = load_agents_from_newest(
        model, model.class_registry, mode=run_mode
    )
    if loaded_file and loaded_id_dict and metadata:
        print(f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}")
        print(f"Metadata: {metadata}")
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
    df_result_dict = model.save_results_as_df()
    final_paths, run_id = model.write_results_csv(df_result_dict)
    for f in final_paths:
        assert f.exists(), print(f"Cannot find file {f}")

    saved_file, metadata = save_agents(model=model, keep_last=5, mode=run_mode)
    assert saved_file.exists() & metadata.exists(), print(
        "Can't find recently saved file"
    )

    # Get the collected data
    model_data = model.datacollector.get_model_vars_dataframe()
    print(f"Total products sold: {int(model_data['Total Products Sales for Today'])}")
    print(f"Total Cust1 sales: ${model_data['Total Cust1 Sales for Today']}")
    print(f"Total Cust2 sales: ${model_data['Total Cust2 Sales for Today']}")
    print(f"Total sales: ${model_data['Total Sales']}")
    print("\nSimulation completed successfully!")

    end = dt.datetime.now()
    duration = end - start
    total_seconds = duration.total_seconds()
    hours = total_seconds // 3600
    minutes = total_seconds // 60 % 60
    seconds = round(total_seconds % 60, 2)
    duration_units = {"h": hours, "m": minutes, "s": seconds}
    print(
        f"Total time taken were: {duration_units['h']} hours {duration_units['m']} minutes {duration_units['s']} seconds"
    )

    return run_id, duration_units


def main():
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="Run simulation for given days based on given number of customers and products",
    )
    parser.add_argument("start_date", type=valid_yyyymmdd, default="Empty")
    parser.add_argument("days", type=int)
    parser.add_argument("customer_num", type=int)
    parser.add_argument("customer_ratio", type=float)
    parser.add_argument("product_num", type=int)

    args = parser.parse_args()
    run_simulation(
        start_date=args.start_date,
        days=args.days,
        total_customers_num=args.customer_num,
        cust1_2_ratio=args.customer_ratio,
        products_num=args.product_num,
    )


if __name__ == "__main__":
    main()
