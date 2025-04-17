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
from datetime import timedelta
import logging

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


# #Customer purchasing categories frequency
# transaction_purchase_behavior = ['productcategory', 'unitprice', 'quantity']

# #Prodcut categories
# product_categories = ['categories', 'discount', 'final_price', 'avg_rating']
# transaction_product_categories = ['productcategory', 'unitprice', 'quantity']
# commerce_product_categories = ['product_line', 'unit_price', 'quantity']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/method/logs/ABM_modeling.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)  # Use the module's name as the logger name
logger.setLevel(logging.INFO)  # Ensure the logger level is set

class Cust1(Agent):
    
    age:int
    gender:str
    city_category:str
    stay_in_current_city_years:int
    marital_status:str
    purchase:gaussian_kde
    product_category:dict
    
    def __init__(self, unique_id:int,
                 segments_dist:dict,
                 cat_dist:dict,
                 num_dist:dict):
        """
        Initialize the customer agent based on walmart customer data.
        """
        self.unique_id = unique_id
        self.segment_id = int(np.random.choice(list(segments_dist.keys()), size=1, p=list(segments_dist.values()))[0])
        
        Demographic = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
        Purchase_behavior = ['product_category', 'purchase']
        
        #Splitting out the product pref with other variables to create new purchases
        cat_num = 0
        for key, value in cat_dist[self.segment_id].items():
            if key.lower() in Demographic:
                setattr(self, key.lower(), np.random.choice(list(value.keys()), size=1, p=list(value.values())))
                cat_num += 1
            elif key.lower() in Purchase_behavior:
                setattr(self, key.lower(), value)
                cat_num += 1
            
        num_num = 0
        for key, value in num_dist[self.segment_id].items():
            if key.lower() in Purchase_behavior:  
                setattr(self, key.lower(), value)
                num_num += 1
        
        assert cat_num + num_num == len(Demographic) + len(Purchase_behavior), 'Number of customer attributes does not match expected'
        
        self.purchase_history = defaultdict(list)
        self.visit_prob = 0.25                                  #default visit probability
        self.budget = self._calculate_budget()
    
    def __repr__(self):
        return f'Cust1({self.unique_id}, {self.age}, {self.gender}, {self.city_category}, {self.stay_in_current_city_years}, {self.marital_status}, {self.product_category}, {self.purchase})'
    
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
        return budget[0][0]
    

    def make_purchase(self, cat_product_list:list, current_date:str):
        """Determine product preference based on learned distributions."""
        choice = str(np.random.choice(list(self.product_category.keys()), size=1, p=list(self.product_category.values()))[0])
        quantity = float(np.random.normal(10, 2, 1)[0])
        unit_price_preference = self.budget / quantity
        
        #Finding the best price match based on category preference
        best_price_match = (None, 0)
        for i in cat_product_list:
            diff = i.unit_price - unit_price_preference
            if best_price_match == (None, 0):
                best_price_match = (i.unique_id, i.unit_price)
            else:
                if diff < best_price_match[1]:
                    best_price_match = (i.unique_id, i.unit_price)
        
        product_id = best_price_match[0]
        unit_price = best_price_match[1]
        total_price = unit_price * quantity
        
        if total_price <= self.budget:
            self.purchase_history[choice].append((product_id, unit_price, quantity, current_date))
        else:
            total_price = unit_price
            self.purchase_history[choice].append((product_id, unit_price, 1, current_date))
        
        return product_id, unit_price, quantity

    
    def step(self, product_list:list, current_date:str):
        """Update customer behavior and preferences."""
        self.budget = self._calculate_budget()
        visit = 1 if random.randint(0, 100) > (self.visit_prob*100) else 0
        
        if visit == 1:
            self.make_purchase(product_list, current_date)
        
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
    
    def __init__(self, unique_id:int,
                 segments_dist:dict,
                 cat_dist:dict,
                 num_dist:dict):
        """
        Initialize the customer agent based on e-commerce transaction data.
        New attributes compared to cust1:
            - date
        """
        self.unique_id = unique_id
        self.segment_id = int(np.random.choice(list(segments_dist.keys()), size=1, p=list(segments_dist.values()))[0])
        
        commerce_demographic_table = ['branch', 'city', 'customer_type', 'gender', 'payment_method']
        commerce_purchase_behavior = ['product_line', 'quantity', 'unit_price', 'date']
        
        cat_num = 0
        for key, value in cat_dist[self.segment_id].items():
            if key.lower() in commerce_demographic_table:
                setattr(self, key.lower(), np.random.choice(list(value.keys()), size=1, p=list(value.values()))[0])
                cat_num += 1
            elif key.lower() in commerce_purchase_behavior:
                setattr(self, key.lower(), value)
                cat_num += 1
                
        num_num = 0
        for key, value in num_dist[self.segment_id].items():
            if key.lower() in commerce_purchase_behavior:
                setattr(self, key.lower(), value)
                num_num += 1
            
        assert cat_num + num_num == len(commerce_demographic_table) + len(commerce_purchase_behavior), f'Number of customer attributes does not match expected: {cat_num} + {num_num} != {len(commerce_demographic_table) + len(commerce_purchase_behavior)}'
        
        self.purchase_history = defaultdict(list)
        self.budget = self._calculate_budget()    
    
    def __repr__(self):
        return f'Cust2({self.unique_id}, {self.branch}, {self.city}, {self.customer_type}, {self.gender}, {self.payment_method}, {self.product_line}, {self.quantity}, {self.unit_price}, {self.date})'
    
    
    
    def get_quantity(self) -> float:
        """Get quantity from either gaussian kde or categorical distribution."""
        if isinstance(self.quantity, gaussian_kde):
            quantity = self.quantity.resample(1)[0][0]
        else:
            quantity = float(np.random.choice(list(self.quantity.keys()), size=1, p=list(self.quantity.values()))[0])
        return quantity
    
    def _calculate_budget(self) -> float:
        """Calculate initial budget based on learned distributions for unit price and quantity."""
        if  len(self.purchase_history) < 5:
            #Checking in case the quantity is numeric instead of categorical
            quantity = self.get_quantity()
            budget = self.unit_price.resample(1)[0][0] * quantity
        else:
            kde = gaussian_kde(self.purchase_history)
            budget = kde.resample(1)[0][0]
        
        return budget
    
    def make_purchase(self, product_list:list, current_date:str):
        """Determine product preference based on learned distributions."""
        choice = str(np.random.choice(list(self.product_line.keys()), size=1, p=list(self.product_line.values()))[0])
        
        #Finding the best price match based on category preference
        best_price_match = (None, 0)
        for i in product_list:
            diff = i.unit_price - self.unit_price
            if best_price_match == (None, 0):
                best_price_match = (i.unique_id, i.unit_price)
            else:
                if diff < best_price_match[1]:
                    best_price_match = (i.unique_id, i.unit_price)
        
        product_id = best_price_match[0]
        unit_price = best_price_match[1]
        quantity = self.get_quantity()
        total_price = unit_price * quantity
        
        if total_price <= self.budget:
            self.purchase_history[choice].append((product_id, unit_price, quantity, current_date))
        else:
            total_price = unit_price
            self.purchase_history[choice].append((product_id, unit_price, 1, current_date))
        
        return product_id, unit_price, quantity
    
    def get_mostcommon_date(self, top_date:int=3) -> list[str]:
        """Pure function to get the most n common date from the date distribution."""
        # sorted_dist = sorted(self.date.items(), key = lambda x: x[1], reverse=True)
        # day_list = [x[0] for x in sorted_dist[0:top_date]]
        return [x[0] for x in sorted(self.date.items(), key = lambda x: x[1], reverse=True)[0:top_date]] 
        

    def step(self, product_list:list, current_date:str):
        """
        Update customer behavior and preferences.
        date: mm/dd/yyyy
        """
        self.budget = self._calculate_budget()
        visit_date = self.get_mostcommon_date()
        
        if current_date in visit_date:
            self.make_purchase(product_list, current_date)

class Product(Agent):
    
    def __init__(self, unique_id:int, product_category:str, 
                 unit_price:float, avg_quantity:float):
        """
        Initialize the product agent.
        """
        self.unique_id = unique_id
        self.product_category = product_category
        self.unit_price = unit_price if unit_price > 0 else 1
        self.annual_demand = avg_quantity * 100 if avg_quantity == 1 else avg_quantity
            
        self.lead_days = int(np.random.normal(7,2,1)[0])  # Convert to int for days
        self.ordering_cost = float(np.random.normal(20,5,1)[0])
        self.holding_cost_per_unit = float(np.random.normal(0.10, 0.02, 1)[0])
        self.EOQ = np.sqrt((2 * self.annual_demand * self.ordering_cost)/ self.holding_cost_per_unit)
        self.stock = self.EOQ
        self.pending_restock_orders = []  # List of (arrival_date, quantity)
        
        self.daily_sales = 0
    
    def __repr__(self):
        return f'Product({self.unique_id}, {self.product_category}, {self.unit_price}, {self.annual_demand})'
        
    def place_restock_order(self, current_date: datetime.datetime):
        """Place a restock order if stock is below threshold."""
        if self.stock < self.EOQ/2:
            restock_amount = self.EOQ
            arrival_date = current_date + timedelta(days=self.lead_days)
            self.pending_restock_orders.append((arrival_date, restock_amount))
        
    def fulfill_restock_orders(self, current_date: datetime.datetime):
        """Fulfill any pending restock orders that have arrived."""
        arrived_orders = [order for order in self.pending_restock_orders 
                         if order[0] <= current_date]

        for arrival_date, quantity in arrived_orders:
            self.stock += quantity

        # Remove fulfilled orders
        self.pending_restock_orders = [
            order for order in self.pending_restock_orders 
            if order[0] > current_date
        ]
    
    def record_sales(self, quantity):
        """Record daily sales."""
        self.daily_sales += quantity
    
    def step(self, current_date: datetime.datetime):
        """Update product state for the current day."""
        self.place_restock_order(current_date)
        self.fulfill_restock_orders(current_date)
        self.stock -= self.daily_sales
        if self.stock < 0:
            self.stock = 0
        self.daily_sales = 0


#Helper functions
def sample_from_distribution(dist, dist_type, n_samples=2):
    try:
        if dist_type == 'kde':
            samples = dist.resample(size=n_samples)[0]
        else:  # normal distribution
            logger.debug(f"Sampling from normal distribution:")
            logger.debug(f"Distribution parameters: loc={dist.kwds.get('loc', 0)}, scale={dist.kwds.get('scale', 1)}")
            samples = dist.rvs(size=n_samples)
            logger.debug(f"Generated samples: {samples}")
        
        # Ensure positive values
        if dist_type == 'kde':
            return max(samples[0], 0.01)  # Minimum price of 0.01
        else:
            return max(samples[0], 1)  # Minimum quantity of 1
    except Exception as e:
        logger.error(f"Error sampling from distribution:")
        logger.error(f"Distribution type: {dist_type}")
        logger.error(f"Distribution object: {dist}")
        logger.error(f"Error: {str(e)}")
        raise

def getting_segments_dist(path):
    """
    Gets customer segment distributions from a dataset and ensures all product categories have probabilities.
    
    This function:
    1. Loads customer segment data containing probabilities, categorical distributions (like product preferences),
       and numerical distributions (like spending patterns) for each customer segment
    2. Reads the product price table to get all possible product categories
    3. For each customer segment, adds any missing product categories with a small probability (0.01)
       and renormalizes the probabilities to sum to 1
    
    Returns:
    - segments_dist: Dict mapping segment IDs to their probabilities
    - segments_cat_dist: Dict mapping segment IDs to their categorical preferences (e.g. product categories)
    - segments_num_dist: Dict mapping segment IDs to their numerical distributions (e.g. spending patterns)
    """
    
    customer_segments_dist, col = dp.get_dataset_distribution(path)
    segments_dist = {int(k): v[0] for k,v in customer_segments_dist.items()}
    segments_cat_dist = {int(k): v[1] for k,v in customer_segments_dist.items()}
    segments_num_dist = {int(k): v[2] for k,v in customer_segments_dist.items()}
    
    print(segments_cat_dist[1])
    print(segments_num_dist[1])
    print(segments_dist[1])
    
    return segments_dist, segments_cat_dist, segments_num_dist
    
def map_cutomerpref_to_all_categories(segments_cat_dist:dict):
    """
    Map customer preferences to all categories.
    Problems:
    - Customer preferences: lowest level category
    - Product price table: highest level category
    Goal:
    - 
    """
    # Read product price table to get all categories
    price_table = pd.read_csv('data_source/product_price_table.csv')
    all_categories = set(price_table['category_path'].unique())
    
    # For each segment, ensure all categories are in preferences
    for segment_id, cat_dist in segments_cat_dist.items():
        if 'product_category' in cat_dist or 'product_line' in cat_dist:
            # Get current category preferences
            current_cats = set(cat_dist.get('product_category', {}).keys()) | set(cat_dist.get('product_line', {}).keys())
            
            
            # Find missing categories
            missing_cats = all_categories - current_cats
            
            # Add missing categories with small probability
            if missing_cats:
                if 'product_category' in cat_dist:
                    for cat in missing_cats:
                        cat_dist['product_category'][cat] = 0.01  # Small probability
                if 'product_line' in cat_dist:
                    for cat in missing_cats:
                        cat_dist['product_line'][cat] = 0.01  # Small probability
                
                # Renormalize probabilities
                if 'product_category' in cat_dist:
                    total = sum(cat_dist['product_category'].values())
                    cat_dist['product_category'] = {k: v/total for k, v in cat_dist['product_category'].items()}
                if 'product_line' in cat_dist:
                    total = sum(cat_dist['product_line'].values())
                    cat_dist['product_line'] = {k: v/total for k, v in cat_dist['product_line'].items()}
    
    return segments_cat_dist

def get_itinerary_category(category:str, item_dict:dict):
    """
    Get all the products containing the category.
    """
    return [x for x in item_dict.values() if category in str(x.product_category)] 

def main():
    #Building the customer agents
    logger.info("Initializing customer agents...")
    segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist("/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/Walmart_cust.csv")
    first_cust = Cust1(unique_id=1, segments_dist=segments_dist, cat_dist=segments_cat_dist, num_dist=segments_num_dist)
    logger.info(f"Created Cust1 with budget: {first_cust.budget}")
    
    segments_dist2, segments_cat_dist2, segments_num_dist2 = getting_segments_dist("/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/Walmart_commerce.csv")
    first_cust2 = Cust2(unique_id=1, segments_dist=segments_dist2, cat_dist=segments_cat_dist2, num_dist=segments_num_dist2)
    logger.info(f"Created Cust2 with budget: {first_cust2.budget}")

    #Building the product agents
    logger.info("Initializing product agents...")
    with open('data_source/category_kde_distributions.pkl', 'rb') as f:
        kde_distributions = pickle.load(f)
    
    # Create product instances
    n = 0
    item_dict = {}
    for category, dist in kde_distributions.items():
        print(category, type(category))
        if category == 'nan':
            continue
        
        logger.info(f"Processing category: {category}")
        logger.debug(f"Price + quantity distribution type: {dist['price_dist_type']} | {dist['quantity_dist_type']}")
        
        # Sample price
        price = sample_from_distribution(dist['price_kde'], dist['price_dist_type'])
        
        # Sample quantity
        quantity = sample_from_distribution(dist['quantity_kde'], dist['quantity_dist_type'])
        
        # Create product instance
        item_dict[n] = Product(
            unique_id=n, 
            product_category=category,
            unit_price=price,
            avg_quantity=quantity
        )
        logger.info(f"Created product {n} with price {price:.2f} and quantity {quantity}")
        n += 1
    
    print('Number of categories: ', len(item_dict))

    # Print first few items to verify
    string = "First 3 product instances:"
    for i in range(min(3, len(item_dict))):
        string += ('\n' + str(item_dict[i]))
    logger.info(string)

    #Making purchases    
    beauty_products = get_itinerary_category('nan', item_dict)
    logger.info(f'Beauty products: {beauty_products}')
    
    product_id, unit_price, quantity = first_cust.make_purchase(beauty_products, '01/01/2024')
    logger.info(f'Product ID: {product_id}, Unit Price: {unit_price}, Quantity: {quantity}')
    
    #Updating the product sales
    beauty_products = [x for x in beauty_products if x.unique_id == product_id]
    beauty_products[0].record_sales(quantity)
    logger.info(f'Daily Sales: {beauty_products[0].daily_sales}')
            
if __name__ == "__main__":
    main()


