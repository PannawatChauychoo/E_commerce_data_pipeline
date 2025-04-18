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
from fuzzywuzzy import process
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

Solutions:
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
                 num_dist:dict,
                 visit_prob:float=0.10):
        """
        Initialize the customer agent based on walmart customer data.
        """
        self.unique_id = unique_id
        self.segment_id = int(np.random.choice(list(segments_dist.keys()), size=1, p=list(segments_dist.values()))[0])
        
        #Getting all attributes from the dataset
        Demographic = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
        Purchase_behavior = ['product_category', 'purchase']
        
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
        
        self.purchase_history = defaultdict(list)       #{category: [(product_id, unit_price, quantity, current_date),...],...}
        self.visit_prob = visit_prob                          #default visit probability
        self.budget = self._calculate_budget()
    
    def __repr__(self):
        return f'Cust1(id:{self.unique_id}, \nage:{self.age}, \ngender:{self.gender}, \ncity_category:{self.city_category}, \nstay_in_current_city_years:{self.stay_in_current_city_years}, \nmarital_status:{self.marital_status}, \nproduct_category:{self.product_category}, \npurchase:{self.purchase})'

    def _calculate_budget(self) -> float:
        """
        Calculate initial budget based on learned distributions.
        Update the probability over time.
        """
        if  len(list(self.purchase_history.values())) < 5:
            budget = self.purchase.resample(1)
        else:
            past_budget = [float(x[1])*float(x[2]) for i in self.purchase_history.values() for x in i]
            kde = gaussian_kde(past_budget)
            budget = kde.resample(1)
            
        #budget = self.purchase.resample(1) 
        return budget[0][0]
    

    def make_purchase(self, cat_product_list:list, current_date:str):
        """
        Determine product preference based on learned distributions.
        Cust1 do not have quantity distribution so will create a random quantity from 0 - 10
        
        Input:
            cat_product_list: list of product agents
            current_date: str of current date
            
        Output:
            product_id: int of product id
            unit_price: float of unit price
            quantity: int of quantity
            
        """
        choice = str(np.random.choice(list(self.product_category.keys()), size=1, p=list(self.product_category.values()))[0])
        quantity = np.random.randint(1, 10)
        unit_price_preference = self.budget / quantity + np.random.normal(0, 1, 1)[0]
        
        #Finding the best price match based on category preference
        best_price_match = 0
        chosen_product_index = 0
        for index, product in enumerate(cat_product_list):
            diff = product.unit_price - unit_price_preference
            if best_price_match == 0:
                best_price_match = product.unit_price
                chosen_product_index = index
            else:
                if diff < best_price_match:
                    best_price_match = product.unit_price
                    chosen_product_index = index
        
        #If the chosen product is out of stock:
        # 4/5 => choose a random product in that category
        # 1/5 => quit the purchase
        if cat_product_list[chosen_product_index].stock == 0:
            quit_prob = random.randint(0, 100)
            if quit_prob > 80:
                return None, None, None
            else:
                chosen_product = random.choice(cat_product_list)
        else:
            chosen_product = cat_product_list[chosen_product_index]
        
        product_id = chosen_product.unique_id
        unit_price = chosen_product.unit_price
        actual_quantity = min(quantity, chosen_product.stock)
        total_price = unit_price * actual_quantity
        
        if self.budget - total_price >= -5:
            self.purchase_history[choice].append((product_id, unit_price, actual_quantity, current_date))
        else:
            total_price = unit_price
            if chosen_product.record_sales(1):
                self.purchase_history[choice].append((product_id, unit_price, 1, current_date))
        
        return product_id, unit_price, actual_quantity

    
    def step(self, product_list:list, current_date:str):
        """Update customer behavior and preferences."""
        self.budget = self._calculate_budget()
        visit = 0 if random.randint(0, 100) > (self.visit_prob*100) else 1
        
        if visit == 1:
            product_id,unit_price, quantity = self.make_purchase(product_list, current_date)
            
            return product_id, quantity
        else:
            return None, None
        
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
                setattr(self, key.lower(), str(np.random.choice(list(value.keys()), size=1, p=list(value.values()))[0]))
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
        return f'Cust2(id:{self.unique_id}, \nbranch:{self.branch}, \ncity:{self.city}, \ncustomer_type:{self.customer_type}, \ngender:{self.gender}, \npayment_method:{self.payment_method}, \nproduct_line:{self.product_line}, \nquantity:{self.quantity}, \nunit_price:{self.unit_price}, \ndate:{self.date})'
    

    def get_quantity(self) -> int:
        """Get quantity from either gaussian kde or categorical distribution."""
        if isinstance(self.quantity, gaussian_kde):
            quantity = int(self.quantity.resample(1)[0][0])
        else:
            quantity = int(np.random.choice(list(self.quantity.keys()), size=1, p=list(self.quantity.values()))[0])
        return quantity
    
    def _calculate_budget(self) -> float:
        """Calculate initial budget based on learned distributions for unit price and quantity."""
        if  len(list(self.purchase_history.values())) < 5:
            #Checking in case the quantity is numeric instead of categorical
            quantity = self.get_quantity()
            budget = self.unit_price.resample(1) * quantity
        else:
            past_budget = [float(x[1])*float(x[2]) for i in self.purchase_history.values() for x in i]
            kde = gaussian_kde(past_budget)
            budget = kde.resample(1)
        
        # quantity = self.get_quantity()
        # budget = self.unit_price.resample(1) * quantity
        return budget[0][0]
    
    def make_purchase(self, cat_product_list:list, current_date:str):
        """
        Determine product preference based on learned distributions.
        Cust2 have quantity distribution so will sample from it.
        
        Input:
            cat_product_list: list of product agents
            current_date: str of current date
            
        Output:
            product_id: int of product id
            unit_price: float of unit price
            quantity: int of quantity
            
        """
        choice = str(np.random.choice(list(self.product_line.keys()), size=1, p=list(self.product_line.values()))[0])
        quantity = self.get_quantity()
        unit_price_preference = self.unit_price.resample(1)[0][0]
        
        #Finding the best price match based on category preference
        best_price_match = 0
        chosen_product_index = 0
        for index, product in enumerate(cat_product_list):
            diff = product.unit_price - unit_price_preference
            if best_price_match == 0:
                best_price_match = product.unit_price
                chosen_product_index = index
            else:
                if diff < best_price_match:
                    best_price_match = product.unit_price
                    chosen_product_index = index
        
        #If the chosen product is out of stock:
        # 4/5 => choose a random product in that category that is in stock
        # 1/5 => quit the purchase
        if cat_product_list[chosen_product_index].stock == 0:
            quit_prob = random.randint(0, 100)
            if quit_prob > 80:
                return None, None, None
            else:
                in_stock_products = [p for p in cat_product_list if p.stock > 0]
                if not in_stock_products:
                    return None, None, None
                chosen_product = random.choice(in_stock_products)
        else:
            chosen_product = cat_product_list[chosen_product_index]
        
        product_id = chosen_product.unique_id
        unit_price = chosen_product.unit_price
        actual_quantity = min(quantity, chosen_product.stock)
        total_price = unit_price * actual_quantity
        
        if self.budget - total_price >= -5:
            if chosen_product.record_sales(actual_quantity):
                self.purchase_history[choice].append((product_id, unit_price, actual_quantity, current_date))
            
            else:
                return None, None, None
        else:
            total_price = unit_price
            if chosen_product.record_sales(1):
                self.purchase_history[choice].append((product_id, unit_price, 1, current_date))
                
            else:
                return None, None, None
        
        return product_id, unit_price, actual_quantity
    
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
        visit_dates = self.get_mostcommon_date()
        date = current_date.split('/')[1]
        
        if date in visit_dates:
            product_id, unit_price, quantity = self.make_purchase(product_list, current_date)
            return product_id, quantity
        else:
            return None, None

class Product(Agent):
    
    def __init__(self, unique_id:int, product_category:str, 
                 unit_price:float, avg_quantity:float):
        """
        Initialize the product agent.
        """
        self.unique_id = unique_id
        self.product_category = product_category
        self.unit_price = unit_price if unit_price > 0 else 1
        self.annual_demand = avg_quantity * 52  # Convert weekly demand to annual
        
        self.lead_days = int(np.random.normal(7,2,1)[0])  # Convert to int for days
        self.ordering_cost = float(np.random.normal(20,5,1)[0])
        self.holding_cost_per_unit = float(np.random.normal(0.10, 0.02, 1)[0])
        self.EOQ = np.sqrt((2 * self.annual_demand * self.ordering_cost)/ self.holding_cost_per_unit)
        self.stock = min(int(self.EOQ), 100)  # Cap initial stock at 100
        self.pending_restock_orders = []  # List of (arrival_date, quantity)
        
        self.daily_sales = 0
        self.total_sales = 0
    
    def __repr__(self):
        return f'Product({self.unique_id}, {self.product_category}, {self.unit_price}, {self.annual_demand})'
        
    def place_restock_order(self, current_date: datetime.datetime):
        """Place a restock order if stock is below threshold."""
        if self.stock < self.EOQ/2:
            restock_amount = min(int(self.EOQ), 50)  # Cap restock amount at 50
            arrival_date = current_date + timedelta(days=self.lead_days)
            self.pending_restock_orders.append((arrival_date, restock_amount))
        
    def fulfill_restock_orders(self, current_date: datetime.datetime):
        """Fulfill any pending restock orders that have arrived."""
        arrived_orders = [order for order in self.pending_restock_orders 
                         if order[0] <= current_date]

        for arrival_date, quantity in arrived_orders:
            #print(f'Fulfilling restock order for product {self.unique_id} on {arrival_date} with quantity {quantity}')
            self.stock += quantity

        # Remove fulfilled orders
        self.pending_restock_orders = [
            order for order in self.pending_restock_orders 
            if order[0] > current_date
        ]
    
    def record_sales(self, quantity):
        """Record daily sales."""
        if self.stock >= quantity:
            self.daily_sales += quantity
            self.total_sales += quantity
            self.stock -= quantity
        else:
            print(f'Product {self.unique_id} is out of stock, selling the remaining {self.stock} out of {quantity}')
            self.daily_sales += self.stock
            self.total_sales += self.stock
            self.stock = 0
    
    def step(self, current_date: datetime.datetime):
        """Update product state for the current day."""
        self.place_restock_order(current_date)
        self.fulfill_restock_orders(current_date)
        self.daily_sales = 0  # Reset daily sales at the end of each day


#Helper functions
def sample_from_distribution(dist, dist_type, n_samples=1):
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
    
    segments_cat_dist = map_cutomerpref_to_all_categories(segments_cat_dist)
    
    return segments_dist, segments_cat_dist, segments_num_dist
    
def map_cutomerpref_to_all_categories(segments_cat_dist:dict):
    """
    Map customer preferences to all categories using fuzzy matching.
    For each customer segment:
    1. Fuzzy match their category preferences to product price table categories
    2. Split probability equally among matching subcategories
    3. Add small probability for unmatched categories
    4. Normalize all probabilities
    """
    # Read product price table to get all categories
    price_table = pd.read_csv('data_source/product_price_table.csv')
    all_categories = price_table['category_path'].unique()
    
    # For each segment, match and redistribute preferences
    for segment_id, cat_dist in segments_cat_dist.items():
        if 'product_category' in cat_dist or 'product_line' in cat_dist:
            # Get current preferences dict
            prefs = cat_dist.get('product_category', {}) or cat_dist.get('product_line', {})
            new_prefs = {}
            
            # For each customer preference category
            for cat, prob in prefs.items():
                # Fuzzy match to find all related categories
                matches = process.extractBests(cat, all_categories, score_cutoff=80)
                
                if matches:
                    # Split probability equally among matches
                    split_prob = prob / len(matches)
                    for match_info in matches:
                        match = match_info[0]  # First element is always the match
                        new_prefs[match] = split_prob
                
            # Add small probability for unmatched categories
            for cat in all_categories:
                if cat not in new_prefs:
                    new_prefs[cat] = 0.01
                    
            # Normalize probabilities
            total = sum(new_prefs.values())
            new_prefs = {k: v/total for k, v in new_prefs.items()}
            
            # Update segment preferences
            if 'product_category' in cat_dist:
                cat_dist['product_category'] = new_prefs
            else:
                cat_dist['product_line'] = new_prefs
    
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


