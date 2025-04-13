import data_processor as dp
import pandas as pd
from mesa import Agent
import random
from scipy.stats import gaussian_kde, norm, uniform
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import datetime

"""
Product table:
- All categories (mapped)
- Price distribution
- Stock level
- Avg rating
- Avg review count


Customer table:
- Behavior table:
    - Budget 
    - Category preference
    - Avg basket size 
    - Avg purchase frequency
    
- Demographic table:
    - Age
    - Gender
    - Location
    - Income
    - Education
    - Occupation
"""

walmart_customer_data_path = "/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/Walmart_customer_data.csv"
customer_segments_dist, customer_segments_col_names = dp.get_dataset_distribution(walmart_customer_data_path)


#Customer demographic table 
cust_demographic_col_names = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
cust_purchase_behavior = ['product_category', 'purchase']


#Customer purchasing categories frequency
commerce_demographic_table = ['branch', 'city', 'customer_type', 'gender', 'payment_method']
commerce_purchase_behavior = ['product_line', 'quantity', 'unit_price', 'date', 'time_of_day', 'day_name']
transaction_purchase_behavior = ['productcategory', 'unitprice', 'quantity']


#Prodcut categories
product_categories = ['categories', 'discount', 'final_price', 'avg_rating']
transaction_product_categories = ['productcategory', 'unitprice', 'quantity']
commerce_product_categories = ['product_line', 'unit_price', 'quantity']


#Customer initialization

    
        
class Cust1(Agent):
    def __init__(self, customer_id:int, segment_id:int, 
                 purchase_dist:gaussian_kde, 
                 category_preference:dict,
                 age:dict, 
                 gender:dict, 
                 city_category:dict, 
                 stay_in_current_city_years:dict, 
                 marital_status:dict):
        """
        Initialize the customer agent based on walmart customer data.
        """
        self.customer_id = customer_id
        self.segment_id = segment_id
        
        self.age = age
        self.gender = gender
        self.city_category = city_category
        self.stay_in_current_city_years = stay_in_current_city_years
        self.marital_status = marital_status
    
        self.purchase_dist = purchase_dist
        self.category_preference = category_preference        
        self.purchase_history = []
        self.visit_prob = 0.25                                  #default visit probability
        self.purchase_history = defaultdict(list)
        self.budget = self._calculate_budget()    
    
    def _calculate_budget(self) -> float:
        """
        Calculate initial budget based on learned distributions.
        Update the probability over time.
        """
        if  len(self.purchase_history) < 5:
            budget = self.purchase_dist.resample(1)
        else:
            kde = gaussian_kde(self.purchase_history)
            budget = kde.resample(1)
        return budget
    

    def make_purchase(self, item_price:dict):
        """Determine product preference based on learned distributions."""
        choice = np.random.choice(list(self.category_preference.keys()), size=1, p=list(self.category_preference.values()))
        unit_price = item_price[choice]
        quantity = np.random.normal(10, 2, 1)
        total_price = unit_price * quantity
        
        if total_price <= self.budget:
            self.purchase_history[choice].append(total_price)
            print(f'{self.customer_id} ought from {choice}')
            return 1 
        else:
            total_price = unit_price
            print(f'Item from {choice} was bigger than budget')
            return 0
    
    def step(self, item_price:dict):
        """Update customer behavior and preferences."""
        self.budget = self._calculate_budget()
        visit = 1 if random.randint(0, 100) > (self.visit_prob*100) else 0
        if visit == 1:
            self.make_purchase(item_price)
        else:
            return f'{self.customer_id} leaving empty'
            
        
    
class Cust2(Agent):
    def __init__(self, customer_id:int, segment_id:int, 
                 purchase_dist:gaussian_kde, 
                 category_preference:dict,
                 branch:dict, 
                 city:dict, 
                 customer_type:dict, 
                 gender:dict, 
                 payment_method:dict,
                 date_dist:dict):
        """
        Initialize the customer agent based on e-commerce transaction data.
        New attributes compared to cust1:
            - date
        """
        
        self.customer_id = customer_id
        self.segment_id = segment_id

        self.branch = branch
        self.city = city
        self.customer_type = customer_type
        self.gender = gender
        self.payment_method = payment_method
        
        self.date_dist = date_dist
        self.purchase_dist = purchase_dist
        self.category_preference = category_preference
        self.purchase_history = defaultdict(list)
        self.budget = self._calculate_budget()    
    
    def _calculate_budget(self) -> float:
        """Calculate initial budget based on learned distributions."""
        if  len(self.purchase_history) < 5:
            budget = self.purchase_dist.resample(1)
        else:
            kde = gaussian_kde(self.purchase_history)
            budget = kde.resample(1)
            
        assert budget > 0, 'budget not created'
        
        return budget
    
    def make_purchase(self, item_price:dict):
        """Determine product preference based on learned distributions."""
        choice = np.random.choice(list(self.category_preference.keys()), size=1, p=list(self.category_preference.values()))
        total_price = item_price[choice]
        if total_price <= self.budget:
            self.purchase_history[choice].append(total_price)
            print(f'Bought from {choice}')
            return 1 
        else:
            print(f'Item from {choice} was bigger than budget')
            return 0
    
    def get_mostcommon_date(self, time_dist:dict, top_date:int=3):
        sorted_dist = sorted(time_dist.items(), key = lambda x: x[1], reverse=True)
        day_list = [x[0] for x in sorted_dist[:top_date-1]]
        return day_list
        

    def step(self, date:str, time:str, item_price:dict):
        """
        Update customer behavior and preferences.
        date: mm/dd/yyyy
        """
        self.budget = self._calculate_budget()
        visit_date = self.get_mostcommon_date(self.date_dist)
        current_date =  date.split('/')[0]
        
        if current_date in visit_date:
            self.make_purchase(item_price)
        else:
            return f'{self.customer_id} leaving empty'    
        
            

class Product(Agent):
    """
    Contains:
        item dict: {cat: kde final price,...} - Final price = Discounted price * quantity
        
        
    """
    
    def __init__(self, product_id:int, product_category:dict, 
                 unit_price:int, avg_rating:float, avg_quantity_dist:dict):
        
        self.product_id = product_id 
        self.product_category = product_category
        self.unit_price = unit_price
        self.avg_rating = avg_rating
        
        self.annual_demand = avg_quantity_dist[product_category].resample(1) #Assuming avg_quantity_dist = {category_name: avg quantiy kde,...}
        self.lead_days = np.random.normal(7,2,1)
        self.ordering_cost = np.random.normal(20,5,1)
        self.holding_cost_per_unit = np.random.normal(0.10, 0.02, 1)
        self.EOQ = np.sqrt((2 * self.annual_demand * self.ordering_cost)/ self.holding_cost_per_unit)
        self.stock = self.EOQ
        self.pending_restock_orders = []
        
        self.daily_sales = 0
        
        
        def place_restock_order(self):
            if self.stock < self.EOQ/2:
                restock_amount = self.EOQ/2
                arrival_step = self.model.schedule.time + self.lead_days
                self.pending_restock_orders.append(arrival_step, restock_amount)
            else:
                pass
            
        def fulfill_restock_orders(self):
            current_step = self.model.schedule.time
            arrived_orders = [order for order in self.pending_restock_orders if order[0] <= current_step]

            for arrival_step, quantity in arrived_orders:
                self.stock += quantity

            # Remove fulfilled orders
            self.pending_restock_orders = [
                order for order in self.pending_restock_orders if order[0] > current_step
            ]
        
        def record_sales(self, quantity):
            self.daily_sales += quantity
        
         
        
        def step(self):
            self.fulfill_restock_orders()
            self.stock -= self.daily_sales
            if self.initial_stock < 0:
                self.initial_stock = 0
            
            self.restock()

            self.daily_sales = 0
    
        
    
        
        
        
        
        
        
        
        

