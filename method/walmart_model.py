from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from walmart_agents import Customer, Product
import random

class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """
    def __init__(self, num_customers=100, num_products=50, width=10, height=10):
        # Initialize model parameters
        self.num_customers = num_customers
        self.num_products = num_products
        self.width = width
        self.height = height
        
        # Set up the grid
        self.grid = MultiGrid(width, height, True)
        
        # Set up the scheduler
        self.schedule = RandomActivation(self)
        
        # Set up the data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Total_Sales": lambda m: sum(agent.sales for agent in m.schedule.agents if hasattr(agent, 'sales')),
                "Customer_Count": lambda m: len([a for a in m.schedule.agents if a.type == "Customer"]),
                "Product_Count": lambda m: len([a for a in m.schedule.agents if a.type == "Product"])
            },
            agent_reporters={
                "Sales": "sales" if hasattr(self, 'sales') else 0,
                "Type": "type"
            }
        )
        
        # Create agents
        self.create_agents()
        self.running = True
        
    def create_agents(self):
        """
        Create customer and product agents.
        """
        # Create customers
        for i in range(self.num_customers):
            # Generate random budget between 50 and 500
            budget = random.randint(50, 500)
            
            # Create customer with random preferences
            preferences = {
                "electronics": random.random(),
                "clothing": random.random(),
                "food": random.random(),
                "home": random.random()
            }
            
            customer = Customer(i, self, budget=budget, preferences=preferences)
            self.schedule.add(customer)
            
            # Place customer in a random cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(customer, (x, y))
        
        # Create products
        product_categories = ["electronics", "clothing", "food", "home"]
        for i in range(self.num_customers, self.num_customers + self.num_products):
            # Generate random product attributes
            name = f"Product_{i-self.num_customers}"
            category = random.choice(product_categories)
            price = random.randint(10, 200)
            inventory = random.randint(50, 200)
            
            product = Product(i, self, name=name, category=category, 
                             price=price, inventory=inventory)
            self.schedule.add(product)
            
            # Place product in a random cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(product, (x, y))
        
    def step(self):
        """
        Advance the model by one step.
        """
        self.datacollector.collect(self)
        self.schedule.step() 