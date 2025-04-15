import data_processor as dp
import pandas as pd
from mesa import Agent
import random
from scipy.stats import gaussian_kde, norm, uniform
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import datetime
import pickle

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
    
Concerns:
- Haven't found a way to include all categories into userpreferences
   - Product: Category, Discount, Final Unit Price, Quantity
   - Customer: Category, Unit Price, Quantity

"""


#Customer purchasing categories frequency
transaction_purchase_behavior = ['productcategory', 'unitprice', 'quantity']


#Prodcut categories
product_categories = ['categories', 'discount', 'final_price', 'avg_rating']
transaction_product_categories = ['productcategory', 'unitprice', 'quantity']
commerce_product_categories = ['product_line', 'unit_price', 'quantity']


#Concerns



#Customer initialization
        
class Cust1(Agent):
    
    age:int
    gender:str
    city_category:str
    stay_in_current_city_years:int
    marital_status:str
    purchase:gaussian_kde
    product_category:dict
    
    def __init__(self, customer_id:int,
                 segments_dist:dict,
                 cat_dist:dict,
                 num_dist:dict):
        """
        Initialize the customer agent based on walmart customer data.
        """
        self.customer_id = customer_id
        self.segment_id = int(np.random.choice(list(segments_dist.keys()), size=1, p=list(segments_dist.values())))
        
        Cat_col = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
        Product_col = ['product_category']
        Num_col = ['purchase']
        
        #Splitting out the product pref with other variables to create new purchases
        cat_num = 0
        for key, value in cat_dist[self.segment_id].items():
            if key.lower() in Cat_col:
                setattr(self, key.lower(), np.random.choice(list(value.keys()), size=1, p=list(value.values())))
                cat_num += 1
            elif key.lower() in Product_col:
                setattr(self, key.lower(), value)
                cat_num += 1
            
        num_num = 0
        for key, value in num_dist[self.segment_id].items():
            setattr(self, key.lower(), value)
            num_num += 1
        
        assert cat_num + num_num == len(Cat_col) + len(Product_col) + len(Num_col), 'Number of customer attributes does not match expected'
        
        self.purchase_history = defaultdict(list)
        self.visit_prob = 0.25                                  #default visit probability
        self.budget = self._calculate_budget()    
    
    def _calculate_budget(self) -> float:
        """
        Calculate initial budget based on learned distributions.
        Update the probability over time.
        """
        if  len(self.purchase_history) < 5:
            budget = self.purchase.resample(1)
        else:
            kde = gaussian_kde(self.purchase_history)
            budget = kde.resample(1)
        return budget[0]
    

    def make_purchase(self, item_price:dict, current_date:str):
        """Determine product preference based on learned distributions."""
        choice = np.random.choice(list(self.product_category.keys()), size=1, p=list(self.product_category.values()))
        unit_price = item_price[choice]
        quantity = np.random.normal(10, 2, 1)
        total_price = unit_price * quantity
        
        if total_price <= self.budget:
            self.purchase_history[choice].append((unit_price, quantity, current_date))
        else:
            total_price = unit_price
            self.purchase_history[choice].append((unit_price, 1, current_date))
        return unit_price, quantity

    
    def step(self, item_price:dict):
        """Update customer behavior and preferences."""
        self.budget = self._calculate_budget()
        visit = 1 if random.randint(0, 100) > (self.visit_prob*100) else 0
        current_date = self.model.current_date.strftime('%m/%d/%Y').split('/')[1]
        
        if visit == 1:
            self.make_purchase(item_price, current_date)
        
class Cust2(Agent):
    
    branch:str
    city:str
    customer_type:str
    gender:str
    payment_method:str
    product_line:dict
    quantity:dict | gaussian_kde
    unit_price:gaussian_kde
    date:dict
    
    def __init__(self, customer_id:int,
                 segments_dist:dict,
                 cat_dist:dict,
                 num_dist:dict):
        """
        Initialize the customer agent based on e-commerce transaction data.
        New attributes compared to cust1:
            - date
        """
        self.customer_id = customer_id
        self.segment_id = int(np.random.choice(list(segments_dist.keys()), size=1, p=list(segments_dist.values())))
        
        commerce_demographic_table = ['branch', 'city', 'customer_type', 'gender', 'payment_method']
        commerce_purchase_behavior = ['product_line', 'quantity', 'unit_price', 'date']
        
        cat_num = 0
        for key, value in segments_cat_dist[self.segment_id].items():
            if key.lower() in commerce_demographic_table:
                setattr(self, key.lower(), np.random.choice(list(value.keys()), size=1, p=list(value.values())))
            elif key.lower() in commerce_purchase_behavior:
                setattr(self, key.lower(), value)
                cat_num += 1
                
        num_num = 0
        for key, value in segments_num_dist[self.segment_id].items():
            setattr(self, key.lower(), value)
            num_num += 1
            
        assert cat_num + num_num == len(commerce_demographic_table) + len(commerce_purchase_behavior), 'Number of customer attributes does not match expected'
        
        self.purchase_history = defaultdict(list)
        self.budget = self._calculate_budget()    
        
    def _get_quantity(self) -> float:
        """Get quantity from either gaussian kde or categorical distribution."""
        if isinstance(self.quantity, gaussian_kde):
            quantity = self.quantity.resample(1)[0]
        else:
            quantity = float(np.random.choice(list(self.quantity.keys()), size=1, p=list(self.quantity.values())))
        return quantity
    
    def _calculate_budget(self) -> float:
        """Calculate initial budget based on learned distributions for unit price and quantity."""
        if  len(self.purchase_history) < 5:
            #Checking in case the quantity is numeric instead of categorical
            quantity = self._get_quantity()
            budget = self.unit_price.resample(1)[0] * quantity
        else:
            kde = gaussian_kde(self.purchase_history)
            budget = kde.resample(1)[0]
            
        assert budget > 0, 'budget not created'
        
        return budget
    
    def make_purchase(self, item_price:dict) -> tuple[float, float]:
        """Determine product preference based on learned distributions."""
        choice = np.random.choice(list(self.product_line.keys()), size=1, p=list(self.product_line.values()))
        unit_price = item_price[choice]
        quantity = self._get_quantity()
        total_price = unit_price * quantity
        
        if total_price <= self.budget:
            self.purchase_history[choice].append((unit_price, quantity))
        else:
            total_price = unit_price
            self.purchase_history[choice].append((unit_price, 1))
        
        assert total_price > 0, 'total price 0 or less'
        
        return unit_price, quantity
    
    def get_mostcommon_date(self, top_date:int=3) -> list[str]:
        """Pure function to get the most n common date from the date distribution."""
        # sorted_dist = sorted(self.date.items(), key = lambda x: x[1], reverse=True)
        # day_list = [x[0] for x in sorted_dist[0:top_date]]
        return [x[0] for x in sorted(self.date.items(), key = lambda x: x[1], reverse=True)[0:top_date]] 
        

    def step(self, item_price:dict):
        """
        Update customer behavior and preferences.
        date: mm/dd/yyyy
        """
        self.budget = self._calculate_budget()
        visit_date = self.get_mostcommon_date()
        current_date =  self.model.current_date.strftime('%m/%d/%Y').split('/')[1]
        
        if current_date in visit_date:
            self.make_purchase(item_price)
        else:
            return f'{self.customer_id} leaving empty'    
        
            

def getting_segments_dist(path):
    """
    segment_format: {segment_name: [
                                    probability, 
                                    {cat_col_name: {value: probability},...}, 
                                    {num_col_name: kde,num_col_name2: kde2,...}
                                    ]}
    """
    
    customer_segments_dist, col = dp.get_dataset_distribution(path)
    segments_dist = {int(k): v[0] for k,v in customer_segments_dist.items()}
    segments_cat_dist = {int(k): v[1] for k,v in customer_segments_dist.items()}
    segments_num_dist = {int(k): v[2] for k,v in customer_segments_dist.items()}
    
    return segments_dist, segments_cat_dist, segments_num_dist

# segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist("/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/Walmart_cust.csv")
# first_cust = Cust1(customer_id=1, segments_dist=segments_dist, cat_dist=segments_cat_dist, num_dist=segments_num_dist)


segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist("/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/Walmart_commerce.csv")



class Product(Agent):
    """
    Contains:
        item dict: {cat: kde final price,...} - Final price = Discounted price * quantity
        
    """
    
    def __init__(self, product_id:int, product_category:str, 
                 unit_price_dist:float, avg_quantity_dist:float):
        
        self.product_id = product_id 
        self.product_category = product_category
        self.unit_price_dist = unit_price_dist
        self.annual_demand = avg_quantity_dist

            
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
            self.place_restock_order()
            self.fulfill_restock_orders()
            self.stock -= self.daily_sales
            if self.initial_stock < 0:
                self.initial_stock = 0
            
            self.restock()

            self.daily_sales = 0

#Building the customer agents


#Building the product agents
with open('data_source/category_kde_distributions.pkl', 'rb') as f:
    kde_distributions = pickle.load(f)

def sample_from_distribution(dist, dist_type, n_samples=1):
    try:
        if dist_type == 'kde':
            samples = dist.resample(size=n_samples)[0]
        else:  # normal distribution
            print(f"\nSampling from normal distribution:")
            print(f"Distribution parameters: loc={dist.kwds.get('loc', 0)}, scale={dist.kwds.get('scale', 1)}")
            samples = dist.rvs(size=n_samples)
            print(f"Generated samples: {samples}")
        
        # Ensure positive values
        if dist_type == 'kde':
            return max(samples[0], 0.01)  # Minimum price of 0.01
        else:
            return max(samples[0], 1)  # Minimum quantity of 1
    except Exception as e:
        print(f"\nError sampling from distribution:")
        print(f"Distribution type: {dist_type}")
        print(f"Distribution object: {dist}")
        print(f"Error: {str(e)}")
        raise

# Create product instances
n = 0
item_dict = {}
for category, dist in kde_distributions.items():
    print(f"\nProcessing category: {category}")
    print(f"Price distribution type: {dist['price_dist_type']}")
    print(f"Quantity distribution type: {dist['quantity_dist_type']}")
    
    # Sample price
    price = sample_from_distribution(dist['price_kde'], dist['price_dist_type'])
    
    # Sample quantity
    quantity = sample_from_distribution(dist['quantity_kde'], dist['quantity_dist_type'])
    
    # Create product instance
    item_dict[n] = Product(
        product_id=n, 
        product_category=category,
        unit_price_dist=price,
        avg_quantity_dist=quantity
    )
    n += 1

# Print first few items to verify
print("\nFirst 3 product instances:")
for i in range(min(3, len(item_dict))):
    print(f"Product {i}:")
    print(f"  Category: {item_dict[i].product_category}")
    print(f"  Unit Price: {item_dict[i].unit_price_dist:.2f}")
    print(f"  Annual Demand: {item_dict[i].annual_demand:.2f}")
    print()

        
        
        


