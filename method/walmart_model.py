from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from walmart_agents import Customer, Product
from data_processor import DistributionAnalyzer
import random
import pandas as pd
from typing import Dict

class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """
    def __init__(self, num_customers=100, num_products=50, width=10, height=10, data_path="../data_source/Walmart_commerce.csv"):
        # Initialize model parameters
        self.num_customers = num_customers
        self.num_products = num_products
        self.width = width
        self.height = height
        
        # Load and process customer data
        self.customer_data = pd.read_csv(data_path, index_col=0)
        self.processor = DistributionAnalyzer(self.customer_data)
        self.processed_data = self.processor.process_data()
        self.cluster_data = self.processor.cluster_data_kmeans(self.processed_data)
        self.cluster_probs = self.processor.analyze_customer_segments_col_dist(self.cluster_data)
        
        # Set up the grid
        self.grid = MultiGrid(width, height, True)
        
        # Set up the scheduler
        self.schedule = RandomActivation(self)
        
        # Set up the data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Total_Sales": lambda m: sum(agent.sales for agent in m.schedule.agents if hasattr(agent, 'sales')),
                "Customer_Count": lambda m: len([a for a in m.schedule.agents if a.type == "Customer"]),
                "Product_Count": lambda m: len([a for a in m.schedule.agents if a.type == "Product"]),
                "Average_Basket_Size": lambda m: self._calculate_avg_basket_size(),
                "Category_Distribution": lambda m: self._get_category_distribution()
            },
            agent_reporters={
                "Sales": "sales" if hasattr(self, 'sales') else 0,
                "Type": "type",
                "Budget": lambda a: a.budget if hasattr(a, 'budget') else 0,
                "Cluster": lambda a: a.attributes.get('cluster', -1) if hasattr(a, 'attributes') else -1
            }
        )
        
        # Create agents
        self.create_agents()
        self.running = True
        
    def _calculate_avg_basket_size(self) -> float:
        """Calculate average basket size across all customers."""
        customers = [a for a in self.schedule.agents if a.type == "Customer"]
        if not customers:
            return 0
        return sum(len(c.purchase_history) for c in customers) / len(customers)
        
    def _get_category_distribution(self) -> Dict[str, float]:
        """Get distribution of purchases across categories."""
        category_sales = {}
        for agent in self.schedule.agents:
            if agent.type == "Product":
                category = agent.category
                category_sales[category] = category_sales.get(category, 0) + agent.sales
        return category_sales
        
    def create_agents(self):
        """
        Create customer and product agents using learned distributions.
        """
        # Create customers from learned distributions
        customer_agents = self.processor.generate_customer_agents(self.num_customers)
        for agent_data in customer_agents:
            behavior_rules = self.processor.get_agent_behavior_rules(agent_data)
            customer = Customer(
                unique_id=agent_data['unique_id'],
                model=self,
                attributes=agent_data['attributes'],
                behavior_rules=behavior_rules
            )
            self.schedule.add(customer)
            
            # Place customer in a random cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(customer, (x, y))
        
        # Create products
        product_categories = list(self.processor.cat_dist_cluster_cols[0].keys())
        for i in range(self.num_customers, self.num_customers + self.num_products):
            # Generate product attributes based on learned distributions
            name = f"Product_{i-self.num_customers}"
            category = random.choice(product_categories)
            
            # Get price from learned distribution if available
            if 'price' in self.processor.kde_cluster_cols[0]:
                price = float(self.processor.kde_cluster_cols[0]['price'].resample(1)[0])
            else:
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