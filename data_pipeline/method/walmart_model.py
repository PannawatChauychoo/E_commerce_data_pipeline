import datetime as dt
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
from ABM_modeling import Cust1, Cust2
from ABM_modeling import Product as ABMProduct
from ABM_modeling import (get_itinerary_category, getting_segments_dist,
                          sample_from_distribution)
from helper.id_tracker import IdRegistry
from helper.save_load import load_agents_from_latest_json, save_agents_to_json
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


datetime_format_str = "%Y/%m/%d"

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
        start_date: datetime,
        max_steps: int = 100,
        n_customers1: int = 100,
        n_customers2: int = 100,
        n_products_per_category: int = 5,
        mode: str = "test",
    ):
        self.schedule = RandomActivation(self)
        self.max_steps = int(max_steps)
        self.current_date = start_date
        self.grid = MultiGrid(1, 1, torus=False)
        self.n_cust1 = n_customers1
        self.n_cust2 = n_customers2
        self.n_prod_per_cat = n_products_per_category
        self.mode = mode

        # Id counter
        self.id_reg = IdRegistry(mode=self.mode)

        # class registry for loading
        self.class_registry = {"Cust1": Cust1, "Cust2": Cust2, "Product": ABMProduct}

        # initialize data collectors
        self.datacollector = DataCollector(
            model_reporters={
                "Current Date": lambda m: m.current_date.strftime(datetime_format_str),
                "Total Sales": lambda m: sum(
                    agent.total_sales
                    for agent in m.schedule.agents
                    if isinstance(agent, ABMProduct)
                ),
                "Total Products Sold": lambda m: sum(
                    agent.total_sales / agent.unit_price
                    for agent in m.schedule.agents
                    if isinstance(agent, ABMProduct)
                ),
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
        Check the added agents match the background index generation.
        Used the  to check all agent classes.

        Input:
            - self.class_registry: {agent_class_name: agent_class_obj,...}
            - self.id_reg.get_id_range: {agent_class_name: [lower_bound, upper_bound],...}
        Output:
            - loaded_mistmatch: {class_name: int(agent id - current agents)} | None if all matches
        """

        # check if agent id within the range for each class
        id_range = self.id_reg.get_id_range()

        current_agent_dict = {}
        for clss_name, clss_obj in self.class_registry.items():
            lower_id_bound, upper_id_bound = id_range[clss_name]
            correctly_loaded_agents = [
                p
                for p in self.schedule.agents
                if isinstance(p, clss_obj)
                and lower_id_bound <= p.unique_id <= upper_id_bound
            ]
            current_agent_dict[clss_name] = len(correctly_loaded_agents)

        print(id_range)
        print(current_agent_dict)
        # comparing agent id count with the number of loaded agent in the model
        loaded = {}
        for k, v in id_range.items():
            id_count = v[1] - v[0]

            if id_count == current_agent_dict[k]:
                print(f"{k}: #id and #current agents matches")
                loaded[k] = id_count
            else:
                raise Exception(f"{k}: Mismatch {id_count} vs {current_agent_dict[k]}")

        return loaded

    def initialize_extra_agents(self):
        # Output: {'Cust1': [id_count, model_loaded_agents],...}
        print("Preload check...")
        loaded = self.check_load_match_index()

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

    def step(self):
        """Advance the model by one day."""
        self.current_date += dt.timedelta(days=1)
        current_date_str = self.current_date.strftime(datetime_format_str)

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
                product_id, quantity = agent.step(
                    choice=choosen_category,
                    product_list=category_products,
                    current_date=current_date_str,
                )
                if product_id is not None and quantity is not None:
                    # print(f"Product {product_id} purchased with quantity {quantity}")
                    total_purchases[product_id] += int(quantity)

        total_daily_sales = 0
        total_daily_products = []

        # Step though all product agents
        for product in products:
            id = product.unique_id
            product_sales = total_purchases.get(id, 0)

            # Update their sales if not empty
            if product_sales != 0:
                product.record_sales(product_sales)
                # print(f"Product {id} total sales: {product_sales}, Unit price: {product.unit_price}")

                total_daily_sales += product.daily_sales
                total_daily_products.append(product.unique_id)

            # Update product state for the current day
            product.step(self.current_date)

        print(f"\nDay {self.schedule.steps} Summary:")
        print(f"Daily Sales: ${total_daily_sales:.2f}")
        print(f"Daily Products Sold: {total_daily_products}")

        # Update scheduler step count
        self.schedule.steps += 1
        self.datacollector.collect(self)

        if self.schedule.steps >= self.max_steps:
            self.running = False

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

        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                for category, purchases in agent.purchase_history.items():
                    for purchase in purchases:
                        transaction_id = self.id_reg.next("total_transaction")
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
                    }
                )

        # Updating for transactions id
        self.id_reg.advance()

        # Saving for SQL
        df_trans = pd.DataFrame(all_transactions)
        df_cust1 = pd.DataFrame(cust1_demographics)
        df_cust2 = pd.DataFrame(cust2_demographics)
        df_product = pd.DataFrame(products)

        final_results_dict = {
            "transaction": df_trans,
            "cust1": df_cust1,
            "cust2": df_cust2,
            "products": df_product,
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

        run_id = uuid.uuid4().int
        run_ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        final_paths = []

        for name, df in df_dict.items():
            # build partition path  e.g. /sim-data/load_dt=2025-06-18/transactions.csv
            saved_file_path = next(root.glob(f"*{name}.csv"), None)
            new_file_path = Path(path) / f"run_time={run_ts}/id={run_id}_{name}.csv"

            if saved_file_path:
                print(saved_file_path)
                df.to_csv(path_or_buf=saved_file_path, mode="a", index=False)
                saved_file_path.rename(new_file_path)
            elif not saved_file_path:
                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(new_file_path, mode="w", index=False)

            print(f"Saving {new_file_path}")
            final_paths.append(new_file_path)

        return final_paths, run_id


def main():
    model = WalmartModel(
        start_date=dt.datetime(2024, 1, 1),
        max_steps=10,
        n_customers1=100,
        n_customers2=100,
        n_products_per_category=5,
        mode="test",
    )
    loaded_file, loaded_id_dict = load_agents_from_latest_json(
        model, model.class_registry, mode="test"
    )
    if loaded_file and loaded_id_dict:
        print(f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}")
    else:
        print("No saved files")

    model.initialize_extra_agents()
    model.run_model()
    saved_file = save_agents_to_json(model, mode="test")
    assert saved_file.exists(), print("Can't find recently saved file")

    df_dict = model.save_results_as_df()
    final_path_list, run_id = model.write_results_csv(df_dict)
    for f in final_path_list:
        assert Path(f).exists(), print(f"Cannot find file {f}")


if __name__ == "__main__":
    main()
