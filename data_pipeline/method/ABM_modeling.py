import data_processor as dp
import pandas as pd
from mesa import Agent
import random
from scipy.stats import gaussian_kde, norm, uniform
import numpy as np
from collections import defaultdict
import datetime
from datetime import timedelta
import logging
from fuzzywuzzy import process
import re
from product_price_table import load_distributions_from_file
from pathlib import Path

"""
Using Monte Carlo to generate customer behavior and preferences based on real distribution from Kaggle datasets

Product table:
- All categories (mapped)
- Price distribution
- Stock level
- Avg rating
- Avg review count

Customer table:
- Cust1
    - Demographic = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
    - Purchase_behavior = ['product_category', 'purchase']
- Cust2
    - Demographic table = ['branch', 'city', 'customer_type', 'gender', 'payment_method']
    - Commerce_purchase_behavior = ['product_line', 'quantity', 'unit_price', 'date']

Helper function:
- sample_from_distribution => get output from kde or frequency dist
- getting_segments_dist => get all distribution for each segment (segment prob, categorical and numeric columns)
- map_cutomerpref_to_all_categories => turn customer preferences to purchase probability for all available categories
- get_itinerary_category => get all products in a category

Concerns:

- There are always manny more factors to consider:
    - I have to backup my simulation choices with tangible data showing some aspects of real data
    - However, validation and verification is one of the greatest challenges in ABM
        - Verification:
            - Document
            - Programmatic testing
        - Validation:
            - Micro-face validation
            - Macro-face validation
            - Empirical input validation
            - Empirical output validation
        

Solutions:
- Including all categories: Splitting the probability of purchases of big categories equally among smaller ones
- 
"""


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/ABM_modeling.log'),
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
        demographic = ['age', 'gender', 'city_category', 'stay_in_current_city_years', 'marital_status']
        purchase_behavior = ['product_category', 'purchase']
        demographic_list = []
        purchase_behavior_list = []
        for key, value in cat_dist[self.segment_id].items():
            key = key.lower()
            if key in demographic:
                if key == 'age':
                    age_range = str(np.random.choice(list(value.keys()), size=1, p=list(value.values()))[0])
                    number_lst = re.findall(r'\d+', age_range)
                    lower, higher = map(int,number_lst) if len(number_lst) == 2 else [int(number_lst[0]), 80]
                    setattr(self, key, int(np.random.randint(lower, higher)))
                    demographic_list.append(key)
                else:
                    setattr(self, key, str(np.random.choice(list(value.keys()), size=1, p=list(value.values()))[0]))
                    demographic_list.append(key)
            elif key in purchase_behavior:
                setattr(self, key, value)
                purchase_behavior_list.append(key)
            
        for key, value in num_dist[self.segment_id].items():
            key = key.lower()
            if key in purchase_behavior:  
                setattr(self, key, value)
                purchase_behavior_list.append(key)
        
        assert len(demographic_list) + len(purchase_behavior_list) == len(demographic) + len(purchase_behavior), f'Cust1: Number of customer attributes ({len(demographic_list)}, {len(purchase_behavior_list)}) does not match expected ({len(demographic)}, {len(purchase_behavior)}): \n {demographic_list} \n {purchase_behavior_list}'
        
        self.purchase_history = defaultdict(list)       #{category: [(product_id, unit_price, quantity, current_date),...],...}
        self.visit_prob = np.random.normal(visit_prob, 0.025)                          #default visit probability
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
    
    def get_category_preference(self):
        """
        Get the category preference based on the learned distributions.
        """
        return str(np.random.choice(list(self.product_category.keys()), size=1, p=list(self.product_category.values()))[0])

    def make_purchase(self, choice:str, cat_product_list:list, current_date:str):
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
            actual_quantity = 1     
            self.purchase_history[choice].append((product_id, unit_price, actual_quantity, current_date))
        
        return product_id, unit_price, actual_quantity
          
    def step(self, choice:str, product_list:list, current_date:str):
        """Update customer behavior and preferences."""
        self.budget = self._calculate_budget()
        visit = 0 if random.randint(0, 100) > (self.visit_prob*100) else 1
        
        if visit == 1:
            product_id,unit_price, quantity = self.make_purchase(choice, product_list, current_date)
            if product_id != None and quantity != None:
                return product_id, quantity
        
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
            
        assert cat_num + num_num == len(commerce_demographic_table) + len(commerce_purchase_behavior), f'Cust2: Number of customer attributes ({cat_num}, {num_num}) does not match expected ({len(commerce_demographic_table)}, {len(commerce_purchase_behavior)})'
        
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
    
    def get_category_preference(self):
        """
        Get the category preference based on the learned distributions.
        """
        return str(np.random.choice(list(self.product_line.keys()), size=1, p=list(self.product_line.values()))[0])
    
    def make_purchase(self, choice:str, cat_product_list:list, current_date:str):
        """
        Most important function in the model: 
        - Determine product preference based on learned distributions.
        - Cust2 have quantity distribution so will sample from it.
        
        Input:
            cat_product_list: list of product agents from the chosen category
            current_date: str of current date
            
        Output:
            product_id: int of product id
            unit_price: float of unit price
            quantity: int of quantity
            
        """
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
            if quit_prob > 60:
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
        # print(f"{self.unique_id} buying {product_id} with quantity {actual_quantity}")
        
        if self.budget - total_price >= -5:
            self.purchase_history[choice].append((product_id, unit_price, actual_quantity, current_date))
        else:
            actual_quantity = 1     
            self.purchase_history[choice].append((product_id, unit_price, actual_quantity, current_date))
        
        return product_id, unit_price, actual_quantity
    
    def get_mostcommon_date(self, top_date:int=3) -> list[str]:
        """Pure function: get the top n common date from the date distribution."""
        return [x[0] for x in sorted(self.date.items(), key = lambda x: x[1], reverse=True)[0:top_date]] 

    def step(self, choice:str, product_list:list, current_date:str):
        """
        Update customer behavior and preferences.
        date: mm/dd/yyyy
        """

        self.budget = self._calculate_budget()
        visit_dates = self.get_mostcommon_date()
        date = current_date.split('/')[1]
        
        if date in visit_dates:
            product_id, unit_price, quantity = self.make_purchase(choice=choice, cat_product_list=product_list, current_date=current_date)
            if product_id != None and quantity != None:
                return product_id, quantity
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
        self.stock = min(int(self.EOQ), 500)  # Cap initial stock at 100
        self.pending_restock_orders = []  # List of (arrival_date, quantity)
        
        self.daily_sales = 0
        self.total_sales = 0
    
    def __repr__(self):
        """For printing the product agent"""
        return f'Product({self.unique_id}, {self.product_category}, {self.unit_price}, {self.annual_demand})'
        
    def place_restock_order(self, current_date: datetime.datetime):
        """Place a restock order if stock is below threshold."""
        if self.stock < self.EOQ/2:
            restock_amount = max(int(self.EOQ), 50)  # Cap restock amount at 50
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

wd = str(Path(__file__).parent)
#Helper functions
def sample_from_distribution(dist, dist_type, n_samples=1) -> float:
    try:
        if dist_type == 'kde':
            samples = dist.resample(size=n_samples)[0]
            return max(samples[0], 1)  # Minimum price of 1
        else:  # normal distribution
            logger.debug(f"Sampling from normal distribution:")
            logger.debug(f"Distribution parameters: loc={dist.kwds.get('loc', 0)}, scale={dist.kwds.get('scale', 1)}")
            samples = dist.rvs(size=n_samples)
            logger.debug(f"Generated samples: {samples}")
            return max(samples[0], 1)  # Minimum quantity of 1
    
    except Exception as e:
        logger.error(f"Error sampling from distribution:")
        logger.error(f"Distribution type: {dist_type}")
        logger.error(f"Distribution object: {dist}")
        logger.error(f"Error: {str(e)}")
        raise

def getting_segments_dist(path) -> tuple[dict[int, float], dict[int, dict[str, float]], dict[int, dict[str, float]]]:
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
    
    assert 'product_category' in segments_cat_dist[1] or 'product_line' in segments_cat_dist[1], f'New product category or product line not found in segments_cat_dist'
    
    return segments_dist, segments_cat_dist, segments_num_dist
    
def map_cutomerpref_to_all_categories(segments_cat_dist:dict) -> dict[int, dict[str, float]]:
    """
    Map customer preferences to all categories using fuzzy matching.
    For each customer segment:
    1. Fuzzy match their category preferences to product price table categories
    2. Split probability equally among smaller subcategories | add smallest category directly
    3. Add small probability for unmatched categories
    4. Normalize all probabilities
    5. Output the final categories (test: # of categories == # of total categories in price table)
    
    Key formatting changes:
    - Convert all keys to lowercase and remove whitespace
    """
    # Read product price table to get all categories
    price_table = pd.read_csv(wd + '/../data_source/product_price_table.csv')
    
    #Getting the main keys and their sub categories in a dict
    categories_dict = {}
    main_key = price_table['category_path'].str.split('>').str[0].unique()
    for k in main_key:
        sub_key = [x.split('>')[-1].strip().lower() for x in price_table['category_path'] if x.startswith(k)]
        key_lower = k.strip().lower()
        if key_lower not in categories_dict:
            categories_dict[key_lower] = sub_key
            
    # For each segment, match and redistribute preferences
    for segment_id, cat_dist in segments_cat_dist.items():
        lower_cat_dist = {k.lower():v for k,v in cat_dist.items()}
        if 'product_category' in lower_cat_dist or 'product_line' in lower_cat_dist:
            # Get current preferences dict
            prefs = lower_cat_dist.get('product_category', {}) or lower_cat_dist.get('product_line', {})
            new_prefs = {}
            
            # For each customer preference category
            for cat, prob in prefs.items():
                # Fuzzy match to find best category match
                cat = cat.lower()
                keys = [x.lower() for x in list(categories_dict.keys())]
                values = [x.lower() for y in list(categories_dict.values()) for x in y]
                main_match = process.extractOne(cat, keys)
                smallest_match = process.extractOne(cat, values)
                
                if main_match:
                    if not smallest_match or main_match[1] > smallest_match[1]:
                        sub_cat = categories_dict[main_match[0]]
                        split_prob = prob / len(sub_cat)
                        new_prefs.update({i: split_prob for i in sub_cat})
                    else:
                        new_prefs[smallest_match[0]] = prob
                elif smallest_match:
                    new_prefs[smallest_match[0]] = prob
                
            # Add small probability for unmatched categories
            for cat in price_table['category_path'].str.split('>').str[-1].unique():
                cat = cat.lower().strip()
                if cat not in new_prefs:
                    new_prefs[cat] = 0.01
                    
            # Normalize probabilities
            total = sum(new_prefs.values())
            new_prefs = {k: v/total for k, v in new_prefs.items()}
            
            # Update segment preferences
            if 'product_category' in lower_cat_dist:
                lower_cat_dist['product_category'] = new_prefs
            else:
                lower_cat_dist['product_line'] = new_prefs
                
        segments_cat_dist[segment_id] = lower_cat_dist

    
    #Checking the output
    if 'product_category' in segments_cat_dist[1]:
        final_categories = set(segments_cat_dist[1]['product_category'].keys())
    else:
        final_categories = set(segments_cat_dist[1]['product_line'].keys())
        
    keys_recorded = set(price_table['category_path'].str.split('>').str[-1].unique())
    assert len(final_categories) == len(keys_recorded), f'Final categories do not match recorded categories'
    
    return segments_cat_dist

def get_itinerary_category(category:str, item_list:list) -> list[Product]:
    """
    Get all the products containing the category.
    """
    return [x for x in item_list if (match := process.extractOne(category, [x.product_category])) and match[1] > 80] 

def main():
    #Building the customer agents
    logger.info("Initializing customer agents...")
    segments_dist, segments_cat_dist, segments_num_dist = getting_segments_dist(wd + "/../data_source/Walmart_cust.csv")
    first_cust = Cust1(unique_id=1, segments_dist=segments_dist, cat_dist=segments_cat_dist, num_dist=segments_num_dist)
    print(first_cust)
    logger.info(f"Created Cust1 with budget: {first_cust.budget}")
    
    segments_dist2, segments_cat_dist2, segments_num_dist2 = getting_segments_dist(wd + "/../data_source/Walmart_commerce.csv")
    first_cust2 = Cust2(unique_id=1, segments_dist=segments_dist2, cat_dist=segments_cat_dist2, num_dist=segments_num_dist2)
    print(first_cust2)
    logger.info(f"Created Cust2 with budget: {first_cust2.budget}")

    #Building the product agents
    logger.info("Initializing product agents...")
    product_dist_path = wd + '/../data_source/category_kde_distributions.npz'
    product_dist_dict = load_distributions_from_file(product_dist_path)
    
    # Create product instances
    n = 0
    item_list = []
    for category, dist in product_dist_dict.items():
        sub_category = category.split('>')[-1].strip().lower()
        
        logger.info(f"Processing category: {sub_category}")
        logger.debug(f"Price + quantity distribution type: {dist['price_dist_type']} | {dist['quantity_dist_type']}")

        n_products = 5
        for _ in range(n_products):
            # Sample price
            price = sample_from_distribution(dist['price_kde'], dist['price_dist_type'])
            # Sample quantity
            quantity = sample_from_distribution(dist['quantity_kde'], dist['quantity_dist_type'])
            # Create product instance
            item_list.append(Product(
                unique_id=n, 
                product_category=sub_category,
                unit_price=price,
                avg_quantity=quantity
            ))
            n += 1
        logger.info(f"Created {n_products} product for {sub_category} with price {price:.2f} and quantity {quantity}")

    # Print first few items to verify
    string = "First 3 product instances:"
    for i in range(min(3, len(item_list))):
        string += ('\n' + str(item_list[i]))
    logger.info(string)

    #Making purchases    
    beauty_products = get_itinerary_category('personal care', item_list)
    logger.info(f'Beauty products: {beauty_products}')
    
    product_id, unit_price, quantity = first_cust.make_purchase(choice='personal care', cat_product_list=beauty_products, current_date='01/01/2024')
    logger.info(f'Product ID: {product_id}, Unit Price: {unit_price}, Quantity: {quantity}')
    
    #Updating the product sales
    beauty_products = [x for x in beauty_products if x.unique_id == product_id]
    beauty_products[0].record_sales(quantity)
    logger.info(f'Daily Sales: {beauty_products[0].daily_sales}')
            
if __name__ == "__main__":
    main()


