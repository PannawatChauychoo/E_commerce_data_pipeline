from mesa import Agent
import random
from typing import Dict, Any

class Customer(Agent):
    """
    A customer agent that makes purchases based on learned behaviors and preferences.
    """
    def __init__(self, unique_id, model, attributes: Dict[str, Any], behavior_rules: Dict[str, Any]):
        super().__init__(unique_id, model)
        self.type = "Customer"
        self.attributes = attributes
        self.behavior_rules = behavior_rules
        self.purchase_history = []
        self.sales = 0
        self.last_purchase = None
        self.budget = self._calculate_budget()
        
    def _calculate_budget(self) -> float:
        """Calculate initial budget based on learned distributions."""
        if 'budget' in self.attributes:
            return float(self.attributes['budget'])
        return random.uniform(50, 500)  # Default range if not learned
        
    def step(self):
        """
        Customer behavior in each step:
        1. Check if it's time to make a purchase based on learned frequency
        2. If yes, make purchase decisions based on learned preferences
        """
        if not self._should_purchase():
            return
            
        # Get available products
        available_products = [agent for agent in self.model.schedule.agents 
                            if agent.type == "Product" and agent.inventory > 0]
        
        if not available_products:
            return
            
        # Select products based on learned preferences
        selected_products = self._select_products(available_products)
        
        # Make purchases within budget
        for product in selected_products:
            if self.budget <= 0:
                break
                
            quantity = self._determine_quantity(product)
            total_cost = product.price * quantity
            
            if total_cost <= self.budget:
                self._make_purchase(product, quantity, total_cost)
                
    def _should_purchase(self) -> bool:
        """Check if customer should make a purchase based on learned frequency."""
        if self.last_purchase is None:
            return True
            
        days_since_last = (self.model.schedule.steps - self.last_purchase)
        return days_since_last >= self.behavior_rules['purchase_frequency']
        
    def _select_products(self, available_products: list) -> list:
        """Select products based on learned preferences."""
        # Sort products by preference score
        scored_products = []
        for product in available_products:
            score = self._calculate_preference_score(product)
            scored_products.append((product, score))
            
        # Sort by score and take top N based on basket size
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in scored_products[:self.behavior_rules['basket_size']]]
        
    def _calculate_preference_score(self, product) -> float:
        """Calculate preference score based on learned category preferences."""
        base_score = self.behavior_rules['category_preferences'].get(product.category, 0.5)
        price_factor = 1 - (self.behavior_rules['price_sensitivity'] * (product.price / 100))
        return base_score * price_factor
        
    def _determine_quantity(self, product) -> int:
        """Determine purchase quantity based on learned behavior."""
        max_affordable = int(self.budget / product.price)
        max_available = min(max_affordable, product.inventory)
        return random.randint(1, max_available)
        
    def _make_purchase(self, product, quantity: int, total_cost: float):
        """Execute the purchase and update relevant attributes."""
        self.budget -= total_cost
        product.inventory -= quantity
        product.sales += total_cost
        self.sales += total_cost
        self.last_purchase = self.model.schedule.steps
        
        self.purchase_history.append({
            "product_id": product.unique_id,
            "quantity": quantity,
            "price": product.price,
            "total": total_cost,
            "step": self.model.schedule.steps
        })
        
        product.popularity += 1


class Product(Agent):
    """
    A product agent that can be purchased by customers.
    """
    def __init__(self, unique_id, model, name="", category="", price=0, inventory=100):
        super().__init__(unique_id, model)
        self.type = "Product"
        self.name = name
        self.category = category
        self.price = price
        self.inventory = inventory
        self.sales = 0
        self.popularity = 0
        
    def step(self):
        """
        Product behavior in each step:
        1. Check inventory levels
        2. Potentially restock if inventory is low
        """
        if self.inventory < 20 and random.random() < 0.5:
            restock_amount = random.randint(50, 100)
            self.inventory += restock_amount 