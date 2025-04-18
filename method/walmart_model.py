from mesa import Model
from mesa.time import RandomActivation # type: ignore
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from walmart_agents import Customer, Product
from data_processor import DistributionAnalyzer
import random
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import pickle
import numpy as np
from ABM_modeling import Cust1, Cust2, Product as ABMProduct, getting_segments_dist, sample_from_distribution
from collections import defaultdict
class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """
    def __init__(self, start_date='01/01/2024', max_steps=100, n_customers=100, n_products_per_category=5):
        self.max_steps = max_steps
        self.schedule = RandomActivation(self)
        self.current_date = datetime.strptime(start_date, '%m/%d/%Y')
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
        self.n_customers = n_customers
        self.n_products_per_category = n_products_per_category
        self._initialize_customers(self.n_customers)
        self._initialize_products(self.n_products_per_category)
        
        self.running = True
        
    def _initialize_customers(self, n_customers):
        """Initialize 100 customers (50 Cust1 and 50 Cust2)."""
        # Initialize Cust1 customers
        segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist("data_source/Walmart_cust.csv")

        for i in range(n_customers//2):
            cust = Cust1(
                unique_id=i,
                segments_dist=segments_dist,
                cat_dist=segments_cat_dist,
                num_dist=segments_num_dist
            )
            if i == 0:
                print(f'First customer: {cust} from Cust1')
            self.schedule.add(cust)
            
        # Initialize Cust2 customers
        segments_dist2, segments_cat_dist2, segments_num_dist2 = getting_segments_dist("data_source/Walmart_commerce.csv")
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
            
    def _initialize_products(self, n_products_per_category):
        """Initialize 5 products for each category."""
        with open('data_source/category_kde_distributions.pkl', 'rb') as f:
            kde_distributions = pickle.load(f)
            
        base_product_id = self.n_customers + 1
        for category, dist in kde_distributions.items():
            if category == 'nan':
                continue
                
            for i in range(n_products_per_category):  # 5 products per category
                price = sample_from_distribution(dist['price_kde'], dist['price_dist_type'])
                quantity = sample_from_distribution(dist['quantity_kde'], dist['quantity_dist_type'])
                
                # Create unique product ID by combining category index and product index
                product_id = base_product_id + i
                
                product = ABMProduct(
                    unique_id=product_id,
                    product_category=category,
                    unit_price=price,
                    avg_quantity=quantity
                )
                
                self.schedule.add(product)
                print(f"Created product {product_id} in category {category} with price {price:.2f}")

            base_product_id += n_products_per_category

        print(f"Total products: {base_product_id - (self.n_customers + 1)}")
        
    def step(self):
        """Advance the model by one step."""
        self.current_date += timedelta(days=1)
        current_date_str = self.current_date.strftime('%m/%d/%Y')
        
        # Get all products
        products = [agent for agent in self.schedule.agents if isinstance(agent, ABMProduct)]
        
        # Step through all customer agents
        total_purchases = defaultdict(int)
        for agent in self.schedule.agents:
            if isinstance(agent, (Cust1, Cust2)):
                product_id, quantity = agent.step(products, current_date_str)
                if product_id is not None and quantity is not None:
                    total_purchases[product_id] += int(quantity)
                    #print(f"Purchase: Product {product_id}, Quantity {quantity}")
        
        total_daily_sales = 0
        total_daily_products = []
        
        # Step though all product agents 
        for product in products:
            id = product.unique_id
            product_sales = total_purchases.get(id, 0)
            
            if id == '675':
                print(product)
            
            # Update their sales if not empty
            if product_sales != 0:
                product.record_sales(product_sales)
                print(f"Product {id} total sales: {product_sales}, Unit price: {product.unit_price}")
  
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
            
    def export_transactions(self):
        """Export transactions to CSV files."""
        cust1_transactions = []
        cust2_transactions = []
        
        for agent in self.schedule.agents:
            if isinstance(agent, Cust1):
                for category, purchases in agent.purchase_history.items():
                    for purchase in purchases:
                        cust1_transactions.append({
                            'unique_id': agent.unique_id,
                            'product_id': purchase[0],
                            'unit_price': purchase[1],
                            'quantity': purchase[2],
                            'date': purchase[3],
                            'category': category
                        })
            elif isinstance(agent, Cust2):
                for category, purchases in agent.purchase_history.items():
                    for purchase in purchases:
                        cust2_transactions.append({
                            'unique_id': agent.unique_id,
                            'product_id': purchase[0],
                            'unit_price': purchase[1],
                            'quantity': purchase[2],
                            'date': purchase[3],
                            'category': category
                        })
                        
        # Convert to DataFrames and export
        pd.DataFrame(cust1_transactions).to_csv('/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/cust1_transactions.csv', index=False)
        pd.DataFrame(cust2_transactions).to_csv('/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/cust2_transactions.csv', index=False)

def main():
    model = WalmartModel(start_date='01/01/2024', max_steps=10, n_customers=500, n_products_per_category=5)
    model.run_model()
    model.export_transactions()

if __name__ == '__main__':
    main()