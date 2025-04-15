from mesa import Model
from mesa.time import RandomActivation # type: ignore
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from walmart_agents import Customer, Product
from data_processor import DistributionAnalyzer
import random
import pandas as pd
from typing import Dict
from datetime import datetime, timedelta

class WalmartModel(Model):
    """
    A model of Walmart e-commerce platform with customers and products.
    """
    def __init__(self, start_date='01/01/2024', max_steps=365):
        self.max_steps = max_steps
        self.schedule = RandomActivation(self)
        self.current_date = datetime.strptime(start_date, '%m/%d/%Y')
        self.grid = MultiGrid(1, 1, torus=False)
        self.datacollector = DataCollector(
            model_reporters={"Current Date": lambda m: m.current_date.strftime('%m/%d/%Y')}
        )
        self.running = True
        
    def step(self):
        self.current_date += timedelta(days=1)
        self.schedule.step()
        self.datacollector.collect(self)
        
        if self.schedule.steps > self.max_steps:
            self.running = False
            
    def run_model(self):
        while self.running:
            self.step()
            