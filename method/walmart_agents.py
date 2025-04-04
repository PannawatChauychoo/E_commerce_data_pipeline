from mesa import Agent
import random

class Customer(Agent):
    """
    A customer agent that makes purchases based on preferences and budget.
    """
    def __init__(self, unique_id, model, budget=100, preferences=None):
        super().__init__(unique_id, model)
        self.type = "Customer"
        self.budget = budget
        self.preferences = preferences or {}
        self.purchase_history = []
        self.sales = 0
        
    def step(self):
        """
        Customer behavior in each step:
        1. Browse available products
        2. Make purchase decisions based on preferences and budget
        """
        # Get available products
        available_products = [agent for agent in self.model.schedule.agents 
                             if agent.type == "Product" and agent.inventory > 0]
        
        if not available_products:
            return
        
        # Decide whether to make a purchase (based on random probability for now)
        if random.random() < 0.3:  # 30% chance to make a purchase
            # Select a product (could be based on preferences)
            product = random.choice(available_products)
            
            # Decide quantity (1-3 items)
            quantity = random.randint(1, min(3, product.inventory))
            
            # Check if within budget
            total_cost = product.price * quantity
            if total_cost <= self.budget:
                # Make the purchase
                self.budget -= total_cost
                product.inventory -= quantity
                product.sales += total_cost
                self.sales += total_cost
                
                # Record purchase
                self.purchase_history.append({
                    "product_id": product.unique_id,
                    "quantity": quantity,
                    "price": product.price,
                    "total": total_cost,
                    "step": self.model.schedule.steps
                })
                
                # Update product popularity
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
        # Restock if inventory is low
        if self.inventory < 20 and random.random() < 0.5:  # 50% chance to restock
            restock_amount = random.randint(50, 100)
            self.inventory += restock_amount 