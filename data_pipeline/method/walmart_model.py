import datetime as dt
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from ABM_modeling import Cust1, Cust2
from ABM_modeling import Product as ABMProduct
from ABM_modeling import (get_itinerary_category, getting_segments_dist,
                          sample_from_distribution)
from helper.datetime_conversion import dt_to_str, str_to_dt
from helper.id_tracker import IdRegistry
from helper.save_load import load_agents_from_newest, save_agents
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from mesa.time import RandomActivation  # type: ignore
from product_price_table import load_distributions_from_file

"""
Imported Product and Customer classes from ABM_modeling.py

Steps for WalmartModel:
- Initialize agents
    - Load past agents
    - Add additional customers based on diff from parameters
    - Add additional products based on diff from parameters
- Step => run a day at a time
- Run model => run model until completion
- Export transactions, customers and products to data_source/agm_output (CSV for now, Parquet later)

Call order:
- load all agent checkpoint from latest simulation -> add additional agents -> run the model -> save agent state -> save csv output

Agent types (includes kde parameters for reconstruction):
- Customer 1 
- Customer 2
- Product

CSV output (only static data):
- Customer1
- Customer2 
- Products
- Transactions

Tracked ID count in id_seeds.json
- Fixed id +1 tracking error

To-do:
- Should add rollback to previous simulation stage -> remove newest saved files and reversed id-tracking
"""

# Always execute this file at data_pipeline directory
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)


class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """

    # wd = str(Path(__file__).parent)

    def __init__(
        self,
        start_date: dt.datetime,
        max_steps: int = 10,
        n_customers1: int = 100,
        n_customers2: int = 100,
        n_products_per_category: int = 5,
        mode: str = "test",
    ):
        self.schedule = RandomActivation(self)
        self.max_steps = max_steps
        self.current_date = (
            str_to_dt(start_date) if isinstance(start_date, str) else start_date
        )
        self.grid = MultiGrid(1, 1, torus=False)
        self.n_cust1 = n_customers1
        self.n_cust2 = n_customers2
        self.n_prod_per_cat = n_products_per_category
        self.mode = mode
        self.run_id = uuid.uuid4().int % (10**8)

        # Id counter
        self.id_reg = IdRegistry(mode=self.mode)

        # class registry for loading
        self.class_registry = {"Cust1": Cust1, "Cust2": Cust2, "Product": ABMProduct}

        """
        Initialize data collectors: 
        - average of purchases value -- line graph
        - total daily purchases -- line graph
        - total number of customers & product -- bar chart
        - stockout rate -- line graph
        """

        self.datacollector = DataCollector(
            model_reporters={
                "Current Date": lambda m: dt_to_str(m.current_date),
                "Total_Cummulative_Sales": lambda m: sum(
                    sum(agent.total_sales.values())
                    for agent in m.schedule.agents
                    if isinstance(agent, ABMProduct)
                ),
                "Total_Cust1_Sales": lambda m: sum(
                    agent.get_total_purchases_by_date(dt_to_str(m.current_date))[0]
                    for agent in m.schedule.agents
                    if isinstance(agent, Cust1)
                ),
                "Avg_Purchases_Cust1": lambda m: np.average(
                    [
                        (
                            agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[0]
                            / agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[1]
                            if isinstance(agent, Cust1)
                            and agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[1]
                            > 0
                            else 0
                        )
                        for agent in m.schedule.agents
                    ]
                ),
                "Total_Cust2_Sales": lambda m: sum(
                    agent.get_total_purchases_by_date(dt_to_str(m.current_date))[0]
                    for agent in m.schedule.agents
                    if isinstance(agent, Cust2)
                ),
                "Avg_Purchases_Cust2": lambda m: np.average(
                    [
                        (
                            agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[0]
                            / agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[1]
                            if isinstance(agent, Cust2)
                            and agent.get_total_purchases_by_date(
                                dt_to_str(m.current_date)
                            )[1]
                            > 0
                            else 0
                        )
                        for agent in m.schedule.agents
                    ]
                ),
                "Total_Daily_Purchase": lambda m: sum(
                    [
                        v
                        for agent in m.schedule.agents
                        if isinstance(agent, ABMProduct)
                        for k, v in agent.total_sales.items()
                        if k == dt_to_str(m.current_date)
                    ]
                ),
                "Total_cust1": lambda m: len(
                    [a for a in m.schedule.agents if isinstance(a, Cust1)]
                ),
                "Total_cust2": lambda m: len(
                    [a for a in m.schedule.agents if isinstance(a, Cust2)]
                ),
                "Total_products": lambda m: len(
                    [a for a in m.schedule.agents if isinstance(a, ABMProduct)]
                ),
                "Stockout": lambda m: len(
                    [
                        p
                        for p in m.schedule.agents
                        if isinstance(p, ABMProduct) and p.stock == 0
                    ]
                )
                / len([a for a in m.schedule.agents if isinstance(a, ABMProduct)]),
            }
        )

        self.running = True

    def add_customers1(self, n_customers1):
        """Initialize 100 customers (50 Cust1 and 50 Cust2)."""

        # Initialize Cust1 customers
        segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist(
            "./data_source/Walmart_cust.csv"
        )

        id_list = []
        for _ in range(n_customers1):
            cust_id = self.id_reg.next("Cust1")
            id_list.append(cust_id)
            cust1 = Cust1(
                unique_id=cust_id,
                segments_dist=segments_dist,
                cat_dist=segments_cat_dist,
                num_dist=segments_num_dist,
                model=self,
                visit_prob=0.10,
            )

            self.schedule.add(cust1)

        try:
            print(f"First Cust1: {self.schedule._agents[id_list[0]]}")
        except IndexError:
            print(f"{id_list[0]} cust1 index doesn't work")

        assert len(id_list) == n_customers1, print(
            f"Cust mismatch: {len(id_list)} vs {n_customers1}"
        )
        print(f"Total added cust1: {(len(id_list))}")

    def add_customers2(self, n_customers2):
        # Initialize Cust2 customers
        segments_dist2, segments_cat_dist2, segments_num_dist2 = getting_segments_dist(
            "./data_source/Walmart_commerce.csv"
        )

        id_list = []
        for _ in range(n_customers2):
            cust_id = self.id_reg.next("Cust2")
            id_list.append(cust_id)
            cust2 = Cust2(
                unique_id=cust_id,
                segments_dist=segments_dist2,
                cat_dist=segments_cat_dist2,
                num_dist=segments_num_dist2,
                model=self,
            )

            self.schedule.add(cust2)

        try:
            print(f"First Cust2: {self.schedule._agents[id_list[0]]}")
        except IndexError:
            print(f"{id_list[0]} cust2 index doesn't work")

        assert len(id_list) == n_customers2, print(
            f"Cust mismatch: {len(id_list)} vs {n_customers2}"
        )
        print(f"Total added cust2: {(len(id_list))}")

    def add_products(self, product_dist_dict, n_products_per_category):
        """Initialize 5 products for each category."""
        id_list = []
        n_categories = 0
        for category, dist in product_dist_dict.items():
            if category == "nan":  # Skip nan categories
                continue
            n_categories += 1

            for _ in range(n_products_per_category):
                price = sample_from_distribution(
                    dist["price_kde"], dist["price_dist_type"]
                )
                quantity = sample_from_distribution(
                    dist["quantity_kde"], dist["quantity_dist_type"]
                )

                product_id = self.id_reg.next("Product")
                id_list.append(product_id)

                product = ABMProduct(
                    unique_id=product_id,
                    product_category=category,
                    unit_price=price,
                    avg_quantity=quantity,
                    model=self,
                )

                self.schedule.add(product)

        try:
            print(f"First product: {self.schedule._agents[id_list[0]]}")
        except IndexError:
            print(f"{id_list[0]} product index doesn't work")

        assert len(id_list) == (n_categories * n_products_per_category), print(
            f"Product mismatch: {len(id_list)} vs {(n_categories * n_products_per_category)}"
        )
        print(f"Total added products: {len(id_list)}")

    def check_load_match_index(self):
        """
        Verify the number of agents loaded for each class matches the ID ranges.

        Inputs:
            - self.class_registry: {class_name: class_obj, ...}
            - self.id_reg.get_id_range(): {class_name: [lower_inclusive, upper_inclusive], ...}
        Output:
            - loaded_counts: {class_name: int}  # actual loaded agents per class
        Raises:
            - Exception with details if any class mismatches
        """
        id_range = self.id_reg.get_id_range()
        loaded_counts = {}
        mismatches = []

        for clss_name, clss_obj in self.class_registry.items():
            if clss_name not in id_range:
                mismatches.append(f"{clss_name}: missing id range")
                continue

            lower, upper = id_range[clss_name]

            # expected count from inclusive range [lower, upper]
            expected = max(0, upper - lower)

            # actual agents loaded with IDs inside the inclusive range
            if upper >= lower:
                actual = sum(
                    1
                    for p in self.schedule.agents
                    if isinstance(p, clss_obj) and lower <= p.unique_id <= upper
                )
            else:
                # No IDs assigned yet => expect 0, actual must be 0
                actual = sum(1 for p in self.schedule.agents if isinstance(p, clss_obj))

            loaded_counts[clss_name] = actual

            if expected != actual:
                current_id = self.id_reg.get_current_id(clss_name)  # could be None
                mismatches.append(
                    f"{clss_name}: expected {expected} (IDs {lower}..{upper}), "
                    f"found {actual}. current_id={current_id}"
                )

        if mismatches:
            raise Exception(
                "ID/agent count mismatch:\n  - " + "\n  - ".join(mismatches)
            )

        # Optional: success logs
        for k, v in loaded_counts.items():
            print(f"{k}: #ids and #current agents match ({v})")

        return loaded_counts

    def initialize_extra_agents(self):
        # Output: {'Cust1': [id_count, model_loaded_agents],...}
        print("Preload check...")
        loaded = self.check_load_match_index()
        print("All id matches!\n")

        # Initialize customers based on previous run agents and new required agents
        diff1 = int(self.n_cust1) - int(loaded["Cust1"])
        diff2 = int(self.n_cust2) - int(loaded["Cust2"])

        if diff1 > 0:
            print(f"Adding: {diff1} Cust1 agents")
            self.add_customers1(diff1)
        else:
            print("No new Cust1 agent added")

        if diff2 > 0:
            print(f"Adding: {diff2} Cust2 agents")
            self.add_customers2(diff2)
        else:
            print("No new Cust2 agent added")

        # Initialize product agents (split equally among all categories) - seems like retail have equal amount of everything
        product_dist_dict = load_distributions_from_file(
            "./data_source/category_kde_distributions.npz"
        )
        total_categories = len(product_dist_dict.keys())
        total_products = total_categories * self.n_prod_per_cat
        diff_prod = int(total_products) - int(loaded["Product"])
        if diff_prod > total_categories:
            extra_prod_per_cat = diff_prod // total_categories
            self.add_products(product_dist_dict, extra_prod_per_cat)
            print(
                f"Adding {diff_prod} products with {extra_prod_per_cat} per categories"
            )
        else:
            print("No new product added")

        return print("Initialization successful for customer1, customer2 and product")

    def get_current_step_metrics_for_graphs(self):
        model_data = self.datacollector.get_model_vars_dataframe()
        latest_row = model_data.iloc[-1]
        return {
            "step": self.schedule.steps,
            "cust1_avg_purchase": float(latest_row.get("Avg_Purchases_Cust1")),
            "cust2_avg_purchase": float(latest_row.get("Avg_Purchases_Cust2")),
            "total_daily_purchases": int(latest_row.get("Total_Daily_Purchase")),
            "total_cust1": int(latest_row.get("Total_cust1")),
            "total_cust2": int(latest_row.get("Total_cust2")),
            "total_products": int(latest_row.get("Total_products")),
            "stockout_rate": float(latest_row.get("Stockout")),
        }

    def step(self):
        """Advance the model by one day."""
        self.current_date += dt.timedelta(days=1)
        current_date_str = dt_to_str(self.current_date)

        # Get all products
        products = [
            agent for agent in self.schedule.agents if isinstance(agent, ABMProduct)
        ]

        # Get all purchases from customer agents
        total_purchases = defaultdict(int)
        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                choosen_category = agent.get_category_preference()
                category_products = get_itinerary_category(choosen_category, products)
                product_id, unit_price, quantity = agent.step(
                    choice=choosen_category,
                    product_list=category_products,
                    current_date=current_date_str,
                )
                if product_id is not None and quantity is not None:
                    # print(f"Product {product_id} purchased with quantity {quantity}")
                    total_purchases[product_id] += int(quantity)

        # Step though all product agents
        for product in products:
            # Update product state for the current day
            product.step(self.current_date)

        # Update scheduler step count
        self.schedule.steps += 1
        self.datacollector.collect(self)
        if self.schedule.steps >= self.max_steps:
            self.running = False

        metrics_dict = self.get_current_step_metrics_for_graphs()
        print(f"\nDay {self.schedule.steps} Summary:")
        print(f"Daily Sales: {metrics_dict["total_daily_purchases"]}")
        print(f"Stockout rate: {metrics_dict["stockout_rate"]}")

        return metrics_dict

    def run_model(self):
        """Run the model until completion."""
        while self.running:
            self.step()

    def save_results_as_df(self) -> dict:
        """
        Save generated transactions, customer and product for partitioned parquet writes.
        - Save demographics/transactions to dataframe for SQL ingestion.
        - Add behaviors, restock orders to above to save agent state for future simulations
        """

        all_transactions = []
        cust1_demographics = []
        cust2_demographics = []
        products = []
        run_id = self.run_id

        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                for category, purchases in agent.purchase_history.items():
                    for purchase in purchases:
                        transaction_id = self.id_reg.next("Transaction")
                        all_transactions.append(
                            {
                                "transaction_id": transaction_id,
                                "unique_id": agent.unique_id,
                                "product_id": purchase[0],
                                "unit_price": purchase[1],
                                "quantity": purchase[2],
                                "date_purchased": purchase[3],
                                "category": category,
                                "cust_type": (
                                    "Cust1" if isinstance(agent, Cust1) else "Cust2"
                                ),
                                "run_id": run_id,
                            }
                        )

                if isinstance(agent, Cust1):
                    cust1_demographics.append(
                        {
                            "unique_id": agent.unique_id,
                            "segment_id": agent.segment_id,
                            "age": agent.age,
                            "gender": agent.gender,
                            "city_category": agent.city_category,
                            "stay_in_current_city_years": agent.stay_in_current_city_years,
                            "marital_status": agent.marital_status,
                            "visit_prob": agent.visit_prob,
                            "run_id": run_id,
                        }
                    )

                elif isinstance(agent, Cust2):
                    cust2_demographics.append(
                        {
                            "unique_id": agent.unique_id,
                            "segment_id": agent.segment_id,
                            "branch": agent.branch,
                            "city": agent.city,
                            "customer_type": agent.customer_type,
                            "gender": agent.gender,
                            "payment_method": agent.payment_method,
                            "run_id": run_id,
                        }
                    )

            elif isinstance(agent, ABMProduct):
                products.append(
                    {
                        "product_id": agent.unique_id,
                        "category": agent.product_category,
                        "unit_price": agent.unit_price,
                        "lead_days": agent.lead_days,
                        "ordering_cost": agent.ordering_cost,
                        "EOQ": agent.EOQ,
                        "stock": agent.stock,
                        "holding_cost_per_unit": agent.holding_cost_per_unit,
                        "run_id": run_id,
                    }
                )

        # Updating for transactions id
        self.id_reg.advance()

        df_metrics = self.datacollector.get_model_vars_dataframe()

        # Saving for SQL
        df_trans = pd.DataFrame(all_transactions)
        df_cust1 = pd.DataFrame(cust1_demographics)
        df_cust2 = pd.DataFrame(cust2_demographics)
        df_product = pd.DataFrame(products)

        final_results_dict = {
            "transactions": df_trans,
            "cust1": df_cust1,
            "cust2": df_cust2,
            "products": df_product,
            "metrics": df_metrics,
        }

        return final_results_dict

    def write_results_csv(self, df_dict: dict[str, pd.DataFrame]):
        """
        Input:
            - df_dict -> output from save_results_as_df
        Save each of the transactions, customers and product dataframe into CSV OR Parquet files.
        - Parquet => Best for columnar data warehouse like ClickHouse or DuckDB.
        - CSV => Best when small, intended for excel analysis and loaded into Postgres
        """

        if self.mode == "test":
            path = "./data_source/agm_output_test"
            print("saving in test folder")
        else:
            path = "./data_source/agm_output"
            print("saving in production folder")

        run_ts = dt.datetime.now().strftime("%Y%m%d")
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        final_paths = []

        for name, df in df_dict.items():
            # /agm_output_test/run_time=2025-06-18/id=123213_transactions.csv
            saved_file_path = next(root.glob(f"run_time={run_ts}/*{name}.csv"), None)
            new_file_path = (
                Path(path) / f"run_time={run_ts}/id={self.run_id}_{name}.csv"
            )

            if saved_file_path:
                print(f"Appending to {saved_file_path}")
                old_df = pd.read_csv(saved_file_path)
                new_rows = df[~df.iloc[:, 0].isin(old_df.iloc[:, 0])]
                new_df = pd.concat([old_df, new_rows], ignore_index=True)
                new_df.to_csv(path_or_buf=saved_file_path, index=False)
                saved_file_path.rename(new_file_path)
            elif not saved_file_path:
                print(f"Saving new file to {new_file_path}")
                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(path_or_buf=new_file_path, mode="w", index=False)

            final_paths.append(new_file_path)

        return final_paths, self.run_id


def main():
    model = WalmartModel(
        start_date=dt.datetime(2024, 1, 1),
        max_steps=10,
        n_customers1=100,
        n_customers2=100,
        n_products_per_category=5,
        mode="test",
    )
    loaded_file, loaded_id_dict, metadata = load_agents_from_newest(
        model, model.class_registry, mode="test"
    )
    if loaded_file and loaded_id_dict:
        print(f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}")
    else:
        print("No saved files")

    model.initialize_extra_agents()
    model.run_model()

    df_dict = model.save_results_as_df()
    final_path_list = model.write_results_csv(df_dict)
    for f in final_path_list:
        assert Path(f).exists(), print(f"Cannot find file {f}")

    saved_file, metadata_file = save_agents(model, mode="test")
    assert saved_file.exists(), print("Can't find recently saved file")


if __name__ == "__main__":
    main()
