import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from typing import Dict, List, Optional
import logging
from sklearn.cluster import KMeans
from collections import defaultdict


class DistributionAnalyzer:
    """
    Analyzes customer data using Kernel Density Estimation.
    """
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with customer data.
        
        Args:
            data: DataFrame containing customer data
        """
        self.data = data
        self.kde_cluster_cols: Dict[int, Dict[str, gaussian_kde]] = defaultdict(lambda: defaultdict(dict))
        self.cat_dist_cluster_cols: Dict[int, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
        self.logger = logging.getLogger(__name__) 
        self.cat_cols = []
        self.num_cols = []

    def process_categorical_data(self, cutoff: int = 20, id_list: list[str] = ['sku', 'id']) -> pd.DataFrame:
        """
        Process categorical data with one hot encoding. Prepare for clustering.
        
        Args:
            cutoff: Minimum number of occurrences for a category to be considered
        Returns:
            pd.DataFrame with one hot encoded categorical data
        """
        
        cat_cols = []
        num_cols = []
        
        for i in self.data.columns:
            # drop id columns
            col = str(i).lower()
            id = False
            for substring in id_list:
                if substring in col:
                    self.data.drop(columns=i, axis = 1,inplace=True)
                    id = True
            
            if id:
                continue    
                
            # check if column contains text/mixed data
            if pd.api.types.is_string_dtype(self.data[i]):
                try:
                    # try converting to numeric - if it fails, it's categorical
                    pd.to_numeric(self.data[i])
                    num_cols.append(i)
                except:
                    cat_cols.append(i)
                    self.data[i] = self.data[i].astype('category')
                    
        print(f'categorical columns are: {cat_cols}')
        print(f'numerical columns are: {num_cols}')
        
        # One-hot encode the categorical columns
        encoded_df = pd.get_dummies(self.data, columns=cat_cols, drop_first=True, dtype=int)   
        self.cat_cols = cat_cols
        self.num_cols = num_cols
        
        return encoded_df
        
        
    def cluster_data_kmeans(self, 
                     encoded_df: pd.DataFrame, 
                     n_clusters: int = 15, 
                     drop_columns: list[str] = []) -> pd.DataFrame:
        """
        Cluster the data using KMeans. Maybe can change to other clustering methods.
        """
        if drop_columns:
            encoded_df = encoded_df.drop(columns=drop_columns, axis = 1)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(encoded_df)
        encoded_df['cluster'] = kmeans.labels_
        return encoded_df
    
    
    def fit_kde(self, 
                column: str, 
                cluster_df: pd.DataFrame,
                cluster_num: int,
                plot: bool = False) -> gaussian_kde:
        """
        Fit a Kernel Density Estimation model to a specific column.
        
        Args:
            column: Name of the column to analyze
            bandwidth: Bandwidth for KDE (if None, use Scott's rule)
            plot: Whether to generate visualization
            
        Returns:
            Fitted KDE model
        """
        print(f'Fitting KDE for column {column} for cluster {cluster_num}...')
        if column not in self.data.columns:
            raise ValueError(f"Column {column} not found in data")
            
        data = np.array(cluster_df[column].dropna().values)
        kde = gaussian_kde(data)
        self.kde_cluster_cols[cluster_num][column] = kde
        
        if plot:
            self._plot_kde(data, kde, column)
            
        return kde
        
    def _plot_kde(self, 
                 data: np.ndarray,
                 kde: gaussian_kde,
                 column: str):
        """
        Plot the data histogram and KDE estimate.
        
        Args:
            data: Data array
            kde: Fitted KDE model
            column: Column name for title
        """
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist(data, bins=30, density=True, alpha=0.6, label='Data')
        
        # Generate KDE estimate
        x = np.linspace(data.min(), data.max(), 200)
        pdf_kde = kde(x)
        
        # Plot KDE
        plt.plot(x, pdf_kde, label='Kernel Density Estimate')
        
        plt.title(f'Kernel Density Estimation - {column}')
        plt.legend()
        plt.grid(True)
        plt.show()
        
    def get_frequency_distribution(self, 
                                   cluster_df: pd.DataFrame, 
                                   cluster_num: int):
        """
        Get the frequency distribution of a categoricalcolumn.
        """
        print(f'Getting all categorical distribution for cluster {cluster_num}...')
        #Getting only the categorical cols
        cat_only_df = cluster_df.drop(columns=self.num_cols, axis = 1)
        cat_dist = cat_only_df.sum()/len(cat_only_df)
        
        #Getting the dist of each column
        for col in self.cat_cols:
            dist = cat_dist[cat_dist.index.str.contains(col)]
            
            cum_prob = 0
            for index, value in dist.items():
                index_num = str(index).split('_')[-1]
                self.cat_dist_cluster_cols[cluster_num][col][index_num] = value
                cum_prob += value
            self.cat_dist_cluster_cols[cluster_num][col]['Remaining'] = 1-cum_prob
        
        return self.cat_dist_cluster_cols
    
    
    def analyze_customer_segments_col_dist(self, 
                                encoded_df: pd.DataFrame):
        """
        Analyze distributions of categorical and numerical columns for each customer.
        
        Args:
            encoded_df: Encoded dataframe with cluster labels
        """
        print('Analyzing customer segments...')
        unique_clusters = encoded_df['cluster'].unique()
        cluster_prob = {}
        for num in unique_clusters:
            cluster_df = encoded_df[encoded_df['cluster'] == num]
            cluster_prob[num] = len(cluster_df)/len(encoded_df)
            #Getting cat dist
            self.get_frequency_distribution(cluster_df, num)
            #Getting num dist
            for col in self.num_cols:
                self.fit_kde(col, cluster_df, num)
                
        return cluster_prob
        
    def generate_synthetic_data(self, 
                                cluster_prob: Dict[int, float],
                                size: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic data based cluster probabilities and each column distribution.
        
        Args:
            cluster_prob: Dictionary of cluster probabilities
            size: Number of samples to generate
            
        Returns:
            DataFrame of synthetic data
        """
        
        # Generate synthetic data for each cluster
        synthetic_data = []
        columns = self.cat_cols + self.num_cols
        
        for _ in range(size):
            cluster_id = np.random.choice(list(cluster_prob.keys()), p=list(cluster_prob.values()))

            #Categorical
            cat_dist = self.cat_dist_cluster_cols[cluster_id]
            cat_values = []
            for col in self.cat_cols:
                dist = cat_dist[col]
                cat = list(dist.keys())
                prob = list(dist.values())
                sample = np.random.choice(cat, p=prob)
                cat_values.append(sample)
            
            #Numerical
            num_values = []
            for col in self.num_cols:
                kde = self.kde_cluster_cols[cluster_id][col]
                samples = kde.resample(1)
                num_values.append(samples)
            
            synthetic_data.append(cat_values + num_values)
            
        return pd.DataFrame(synthetic_data, columns=columns)

def main():
    # Read data from csv
    data = pd.read_csv('../data_source/Walmart_cust.csv')
    print(data.info())
    
    # Initialize processor
    processor = DistributionAnalyzer(data)
    processed_data = processor.process_categorical_data()
    print(processor.cat_cols)
    print(processor.num_cols)
    cluster_data = processor.cluster_data_kmeans(processed_data)
    cluster_probs = processor.analyze_customer_segments_col_dist(cluster_data)
    
    # Generate synthetic data
    synthetic_df = processor.generate_synthetic_data(cluster_probs, size=50)
    
    # Print sample of original vs synthetic
    print("\nOriginal Data Sample:")
    print(data.head())
    print("\nSynthetic Data Sample:") 
    print(synthetic_df.head())

   
if __name__ == "__main__":
    main() 