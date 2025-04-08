import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from typing import Dict, List, Optional
import logging
from sklearn.cluster import KMeans
from collections import defaultdict
from dateutil.parser import parse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_processing.log'),
        logging.StreamHandler()
    ]
)

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
        self.cat_cols = []
        self.num_cols = []
        self.id_cols = []
        self.datetime_cols = []
        self.logger = logging.getLogger(__name__)
        self.logger.info("DistributionAnalyzer initialized with data shape: %s", data.shape)

    def _is_date(self, value: str) -> bool:
        """Check if a string can be parsed as a date."""
        try:
            parse(value, fuzzy=True)
            return True
        except (ValueError, TypeError):
            return False

    def process_dataset(self, cutoff: float = 50, id_list: list[str] = ['sku', 'id']) -> pd.DataFrame:
        """
        Process data with one hot encoding. Prepare for clustering.
        
        Args:
            cutoff: Minimum number of occurrences for a category to be considered
            id_list: List of substrings to identify ID columns
            
        Returns:
            pd.DataFrame with processed data
        """
        self.logger.info("Starting data processing with cutoff: %s", cutoff)
        cat_cols: list[str] = []
        num_cols: list[str] = []
        id_cols: list[str] = []
        datetime_cols: list[str] = []

        for i in self.data.columns:
            col = str(i).lower()
            id = False
            
            # Check for ID columns
            if any(word in col for word in id_list) or self.data[i].nunique() == len(self.data):
                id_cols.append(i)
                id = True
                self.logger.debug("Identified ID column: %s", i)

            if id:
                continue

            # Check for datetime columns
            if self.data[i].dtype == 'object':
                sample_size = min(100, len(self.data[i]))
                date_count = sum(self._is_date(str(x)) for x in self.data[i].head(sample_size))
                if date_count / sample_size > 0.8:  # If 80% of samples are dates
                    if '-' in self.data[i][0] or ':' in self.data[i][0]:
                        datetime_cols.append(i)
                        self.logger.debug("Added datetime column: %s", i)
                        continue
                    else:
                        cat_cols.append(i)
                        self.logger.debug("Added singledatetime column as categorical: %s", i)
                        continue

            # Check for categorical or numerical columns
            if self.data[i].nunique() <= cutoff:
                cat_cols.append(i)
                self.logger.debug("Added categorical column: %s", i)
            else:
                num_cols.append(i)
                self.logger.debug("Added numerical column: %s", i)

        self.logger.info("Found: \n %s as categorical columns, \n %s as numerical columns, \n %s as ID columns, \n %s as datetime columns", 
                        cat_cols, num_cols, id_cols, datetime_cols)

        assert len(cat_cols+num_cols+id_cols+datetime_cols) == len(self.data.columns), \
            f'Some columns are missing. Original: {len(self.data.columns)}, Final: {len(cat_cols+num_cols+id_cols+datetime_cols)}'

        self.cat_cols = cat_cols
        self.num_cols = num_cols
        self.id_cols = id_cols
        self.datetime_cols = datetime_cols

        # One-hot encode categorical columns
        encoded_df = pd.get_dummies(self.data, columns=cat_cols, dtype=int)
        return encoded_df
        
        
    def cluster_data_kmeans(self, 
                            encoded_df: pd.DataFrame, 
                            n_clusters: int = 15, 
                            drop_columns: list[str] = []) -> pd.DataFrame:
        """
        Cluster the data using KMeans. Maybe can change to other clustering methods.
        """
        drop_columns = drop_columns + self.datetime_cols + self.id_cols
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
        self.logger.info("Fitting KDE for column %s in cluster %d", column, cluster_num)
        if column not in self.data.columns:
            self.logger.error("Column %s not found in data", column)
            raise ValueError(f"Column {column} not found in data")
            
        data = np.array(cluster_df[column].dropna().values)
        kde = gaussian_kde(data)
        self.kde_cluster_cols[cluster_num][column] = kde
        self.logger.debug("KDE fitted successfully for column %s", column)
        
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
        Get the frequency distribution of a categorical column.
        """
        self.logger.info("Getting all categorical distribution for cluster %d", cluster_num)
        #Getting only the categorical cols
        cat_only_df = cluster_df.drop(columns=self.num_cols, axis = 1)
        cat_dist = cat_only_df.sum()/len(cat_only_df)
        
        #Getting the dist of each column
        for col in self.cat_cols:
            dist = cat_dist[cat_dist.index.str.contains(col)]
            
            for index, value in dist.items():
                categories = str(index).split('_')[-1]
                self.cat_dist_cluster_cols[cluster_num][col][categories] = value
        return self.cat_dist_cluster_cols
    
    
    def analyze_segments_col_dist(self, 
                                encoded_df: pd.DataFrame):
        """
        Analyze distributions of categorical and numerical columns for each customer.
        
        Args:
            encoded_df: Encoded dataframe with cluster labels
        """
        self.logger.info("Analyzing customer segments...")
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
    # Configure logging for main
    logger = logging.getLogger(__name__)
    logger.info("Starting data processing pipeline")
    
    try:
        # Read data from csv
        data = pd.read_csv('../data_source/Walmart_commerce.csv', index_col=0)
        logger.info(f"Data loaded successfully. Info: {data.info()}")        
        
        # Initialize processor
        processor = DistributionAnalyzer(data)
        processed_data = processor.process_dataset()
        logger.info("Categorical data processing completed")
        
        cluster_data = processor.cluster_data_kmeans(processed_data)
        logger.info("Clustering completed. Found %d clusters", len(cluster_data['cluster'].unique()))
        
        cluster_probs = processor.analyze_segments_col_dist(cluster_data)
        logger.info("Customer segment analysis completed")
        
        # Generate synthetic data
        synthetic_df = processor.generate_synthetic_data(cluster_probs, size=50)
        logger.info("Synthetic data generation completed. Generated %d samples", len(synthetic_df))
        
    except Exception as e:
        logger.error("Error in data processing pipeline: %s", str(e), exc_info=True)
        raise

if __name__ == "__main__":
    main() 