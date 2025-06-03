from mesa import Model
from mesa.time import RandomActivation # type: ignore
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from data_processor import DistributionAnalyzer
import random
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import pickle
import numpy as np
from ABM_modeling import Cust1, Cust2, Product as ABMProduct, getting_segments_dist, sample_from_distribution, get_itinerary_category
from collections import defaultdict
from product_price_table import load_distributions_from_file
from pathlib import Path
"""
Steps for WalmartModel:
- Initialize customers
- Initialize products
- Step => run a day at a time
- Run model => run model until completion
- Export transactions, customers and products to data_source/agm_output
"""


class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """
    wd = str(Path(__file__).parent)
    
    def __init__(self, start_date, max_steps=100, n_customers=100, n_products_per_category=5):
        self.schedule = RandomActivation(self)
        self.max_steps = int(max_steps)
        self.current_date: datetime = datetime.strptime(start_date, '%m/%d/%Y') if type(start_date) == str else start_date
        self.grid = MultiGrid(1, 1, torus=False)
        
        # Initialize data collectors
        self.datacollector = DataCollector(
            model_reporters={
                "Current Date": lambda m: m.current_date.strftime('%m/%d/%Y'),
                "Total Sales": lambda m: sum(agent.total_sales for agent in m.schedule.agents if isinstance(agent, ABMProduct)),
                "Total Products Sold": lambda m: sum(agent.total_sales/agent.unit_price for agent in m.schedule.agents if isinstance(agent, ABMProduct))
            }
        )
        
        # Initialize customers and products
        self.n_customers = int(n_customers)
        self.n_products_per_category = int(n_products_per_category)
        self._initialize_customers(self.n_customers)
        self._initialize_products(self.n_products_per_category)
        
        self.running = True
        
    def _initialize_customers(self, n_customers):
        """Initialize 100 customers (50 Cust1 and 50 Cust2)."""
        # Initialize Cust1 customers
        segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist(self.wd + "/../data_source/Walmart_cust.csv")
        for i in range(n_customers//2):
            cust = Cust1(
                unique_id=i,
                segments_dist=segments_dist,
                cat_dist=segments_cat_dist,
                num_dist=segments_num_dist,
                visit_prob=0.10
            )
            if i == 0:
                print(f'First customer: {cust} from Cust1')
            self.schedule.add(cust)
            
        # Initialize Cust2 customers
        segments_dist2, segments_cat_dist2, segments_num_dist2 = getting_segments_dist(self.wd + "/../data_source/Walmart_commerce.csv")
        for i in range(n_customers//2, n_customers):
            cust = Cust2(
                unique_id=i,
                segments_dist=segments_dist2,
                cat_dist=segments_cat_dist2,
                num_dist=segments_num_dist2
            )
            
            if i == n_customers//2:
                print(f'First customer: {cust} from Cust2')
            self.schedule.add(cust)
        
        print(f"Total customers: {len(self.schedule.agents)}")
    
    #Todo: Fix the repeated product ID
    def _initialize_products(self, n_products_per_category):
        """Initialize 5 products for each category."""
        
        product_dist_dict = load_distributions_from_file(self.wd +  '/../data_source/category_kde_distributions.npz')
            
        base_product_id = self.n_customers + 1
        for category, dist in product_dist_dict.items():
            if category == 'nan':  # Skip nan categories
                continue
            for i in range(n_products_per_category):
                price = sample_from_distribution(dist['price_kde'], dist['price_dist_type'])
                quantity = sample_from_distribution(dist['quantity_kde'], dist['quantity_dist_type'])
                
                product = ABMProduct(
                    unique_id=base_product_id,
                    product_category=category,
                    unit_price=price,
                    avg_quantity=quantity
                )
                
                self.schedule.add(product)
                base_product_id += 1
                #print(f"Created product {base_product_id-1} in category {category} with price {price:.2f}")

        print(f"Total products: {base_product_id - (self.n_customers + 1)}")
        
    def step(self):
        """Advance the model by one day."""
        self.current_date += timedelta(days=1)
        current_date_str = self.current_date.strftime('%m/%d/%Y')
        
        # Get all products
        products = [agent for agent in self.schedule.agents if isinstance(agent, ABMProduct)]
        
        # Get all purchases from customer agents
        total_purchases = defaultdict(int)
        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                choosen_category = agent.get_category_preference()
                category_products = get_itinerary_category(choosen_category, products)
                product_id, quantity = agent.step(choice=choosen_category, product_list=category_products, current_date=current_date_str)
                if product_id is not None and quantity is not None:
                    #print(f"Product {product_id} purchased with quantity {quantity}")
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
                #print(f"Product {id} total sales: {product_sales}, Unit price: {product.unit_price}")
  
                total_daily_sales += product.daily_sales * product.unit_price 
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
        
    def export_transactions(self, path):
        """Export transactions to CSV files."""
        all_transactions = []
        
        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                for category, purchases in agent.purchase_history.items():
                    for purchase in purchases:
                        all_transactions.append({
                            'unique_id': agent.unique_id,
                            'product_id': purchase[0],
                            'unit_price': purchase[1],
                            'quantity': purchase[2],
                            'date_purchased': purchase[3],
                            'category': category,
                            'cust_type': 'Cust1' if isinstance(agent, Cust1) else 'Cust2'
                    })

        # Convert to DataFrames and export
        pd.DataFrame(all_transactions).to_csv(path, mode="a", index=False, header=False)

    def export_demographics(self, path1, path2):
        """Export customer demographics to CSV files."""
        cust1_demographics = []
        cust2_demographics = []
        
        for agent in self.schedule.agents:
            if isinstance(agent, Cust1):
                cust1_demographics.append({
                    'unique_id': agent.unique_id,
                    'age': agent.age,
                    'gender': agent.gender,
                    'city_category': agent.city_category,
                    'stay_in_current_city_years': agent.stay_in_current_city_years,
                    'marital_status': agent.marital_status,
                    'segment_id': agent.segment_id,
                    'visit_prob': agent.visit_prob
                })
            elif isinstance(agent, Cust2):
                cust2_demographics.append({
                    'unique_id': agent.unique_id,
                    'branch': agent.branch,
                    'city': agent.city,
                    'customer_type': agent.customer_type,
                    'gender': agent.gender,
                    'payment_method': agent.payment_method,
                    'segment_id': agent.segment_id
                })
         
        # Convert to df to csv and append to current csv
        pd.DataFrame(cust1_demographics).to_csv(path1,  mode="a", index=False, header=False)
        pd.DataFrame(cust2_demographics).to_csv(path2,  mode="a", index=False, header=False)

    def export_products(self, path):
        """Export products to CSV files."""
        products = []
        for agent in self.schedule.agents:
            if isinstance(agent, ABMProduct):
                products.append({
                    'product_id': agent.unique_id,
                    'category': agent.product_category,
                    'unit_price': agent.unit_price,
                    'stock': agent.stock,
                    'lead_days': agent.lead_days,
                    'ordering_cost': agent.ordering_cost,
                    'holding_cost_per_unit': agent.holding_cost_per_unit,
                    'EOQ': agent.EOQ
                })
        
        # Convert to df to csv and append to current csv
        pd.DataFrame(products).to_csv(path,  mode="a", index=False, header=False)
        
def main():
    model = WalmartModel(start_date='01/01/2024', max_steps=10, n_customers=100, n_products_per_category=15)
    model.run_model()


if __name__ == '__main__':
    main()