import pandas as pd
from typing import List, Dict, Tuple
import re
from fuzzywuzzy import fuzz

class ProductCategorizer:
    def __init__(self):
        # Define main categories and their keywords
        self.categories = {
            'Snacks': {
                'Chocolate & Candy': ['chocolate', 'candy', 'smarties', 'bar', 'cookie', 'cookies'],
                'Chips & Crackers': ['chips', 'crackers', 'doritos', 'nacho'],
                'Other Snacks': ['popcorn', 'nuts', 'trail mix', 'snack']
            },
            'Beverages': {
                'Alcoholic': ['wine', 'beer', 'vodka', 'rum', 'whiskey', 'whisky', 'liqueur', 'brandy', 'tequila'],
                'Non-Alcoholic': ['juice', 'tea', 'coffee', 'water', 'soda', 'lemonade', 'drink', 'rootbeer'],
            },
            'Meat & Seafood': {
                'Fish': ['cod', 'fish', 'salmon', 'tuna', 'trout', 'halibut'],
                'Shellfish': ['clam', 'shrimp', 'lobster', 'crab', 'scallop'],
                'Poultry': ['chicken', 'turkey', 'fowl', 'quail'],
                'Red Meat': ['beef', 'pork', 'lamb', 'veal', 'bacon', 'sausage']
            },
            'Produce': {
                'Fruits': ['apple', 'orange', 'banana', 'berry', 'fruit', 'lemon', 'lime', 'mango', 
                          'melon', 'pear', 'grape', 'cherry'],
                'Vegetables': ['lettuce', 'tomato', 'pepper', 'onion', 'potato', 'carrot', 'vegetable',
                             'cucumber', 'zucchini', 'eggplant', 'squash']
            },
            'Dairy & Eggs': {
                'Dairy': ['cheese', 'milk', 'cream', 'yogurt', 'butter', 'egg']
            },
            'Bakery': {
                'Products': ['bread', 'roll', 'bagel', 'muffin', 'pastry', 'cake']
            },
            'Pantry': {
                'Condiments': ['sauce', 'mustard', 'mayo', 'dressing', 'vinegar', 'oil'],
                'Spices': ['spice', 'pepper', 'salt', 'seasoning', 'herb'],
                'Dry Goods': ['flour', 'sugar', 'rice', 'pasta', 'cereal']
            },
            'Prepared Foods': {
                'Pre-made': ['soup', 'salad', 'prepared', 'ready', 'mix']
            },
            'Non-Food Items': {
                'Items': ['cup', 'paper', 'cleaner', 'soap', 'towel', 'container', 'bag', 'glove']
            }
        }
    
    
    def _normalize_text(self, text: str) -> Tuple[str, str]:
        """
        Normalize text and extract the primary word for categorization.
        Returns tuple of (primary_word, full_normalized_text)
        """
        # Convert to lowercase and remove special characters except hyphens
        normalized = text.lower().strip()
        
        # Handle special cases with hyphen
        if '-' in normalized:
            parts = normalized.split('-')
            primary_word = parts[0].strip()
            # Special case for non-food items that might have meaningful second parts
            return primary_word, primary_word
        
        if any(word in normalized for word in ['cup', 'container', 'bag', 'towel']):
            primary_word = [word for word in ['cup', 'container', 'bag', 'towel'] if word in normalized][0]
            return primary_word, normalized
        
        # Remove other punctuation for the full text
        full_text = re.sub(r'[^\w\s]', ' ', normalized)
        primary_word = full_text.split()[0] if full_text else ''
        
        return primary_word, full_text
    
    def _get_fuzzy_match_score(self, text: str, keyword: str) -> int:
        """Get fuzzy matching score between text and keyword."""
        # Exact match gets highest score
        if text == keyword:
            return 100
        # Primary word match gets high score
        if text.split()[0] == keyword:
            return 90
        # Fuzzy match for other cases
        return fuzz.partial_ratio(text, keyword)
    

    
    def categorize_product(self, product_name: str) -> Dict[str, str | int]:
        """Categorize a single product name."""
        primary_word, normalized_name = self._normalize_text(product_name)
               
        best_match = {
            'main_category': 'Uncategorized',
            'sub_category': 'Uncategorized',
            'confidence': 0
        }
        
        # First try to match based on the primary word
        for main_cat, sub_cats in self.categories.items():
            for sub_cat, keywords in sub_cats.items():
                if isinstance(keywords, list):
                    if primary_word in keywords:
                        return {
                            'main_category': main_cat,
                            'sub_category': sub_cat,
                            'confidence': 100
                        }
        
        # If no exact match found, try fuzzy matching on the full normalized name
        for main_cat, sub_cats in self.categories.items():
            for sub_cat, keywords in sub_cats.items():
                if isinstance(keywords, list):
                    for keyword in keywords:
                        score = self._get_fuzzy_match_score(normalized_name, keyword)
                        if score > best_match['confidence']:
                            best_match = {
                                'main_category': main_cat,
                                'sub_category': sub_cat,
                                'confidence': score
                            }
        
        # Handle special cases and edge cases
        if best_match['confidence'] < 60:
            # Check for specific patterns in the full product name
            if any(word in normalized_name for word in ['container', 'bag', 'glove', 'cleaner']):
                best_match['main_category'] = 'Non-Food Items'
                best_match['sub_category'] = 'Supplies'
                best_match['confidence'] = 90
            # Handle food containers
            elif 'cup' in normalized_name:
                best_match['main_category'] = 'Non-Food Items'
                best_match['sub_category'] = 'Food Service'
                best_match['confidence'] = 85
            else:
                best_match['main_category'] = 'Uncategorized'
                best_match['sub_category'] = 'Low Confidence'
                best_match['confidence'] = 30
                
        return best_match

    def categorize_products(self, products: List[str]) -> pd.DataFrame:
        """Categorize a list of products."""
        results = []
        for product in products:
            if pd.isna(product):  # Handle NaN values
                results.append({
                    'product': product,
                    'main_category': 'Invalid',
                    'sub_category': 'Invalid',
                    'confidence': 0
                })
                continue
                
            categorization = self.categorize_product(product)
            results.append({
                'product': product,
                'main_category': categorization['main_category'],
                'sub_category': categorization['sub_category'],
                'confidence': categorization['confidence'],
                'primary_word': self._normalize_text(product)[0]  # Add primary word for verification
            })
            
        return pd.DataFrame(results)

# Example usage
if __name__ == "__main__":
    # Sample data with edge cases
    sample_products = [
        "Chocolate Bar - Smarties",
        "Coffee Cup 8oz 5338cd",
        "Cod - Salted, Boneless",
        "Clam - Cherrystone",
        "Wine - Red, Merlot",
        "Chicken - Whole Roasting",
        "Bread - Multigrain",
        "Paper Towel",
        "Soup - Campbells, Beef Barley"
    ]
    
    categorizer = ProductCategorizer()
    results = categorizer.categorize_products(sample_products)
    print(results[['product', 'main_category', 'sub_category', 'confidence', 'primary_word']]) 