import logging
import random
from collections import defaultdict
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.parser import parse
from scipy.stats import gaussian_kde
from sklearn.cluster import KMeans

"""
Goal: Find the distribution of each column in the csv file after clustering with k-means

Steps:
1. Process dataset by identifying the type of each column (categoric, numeric, id, datetime, text)
2. Fit kmeans on categorical and numeric columns to get clusters
3. Get distribution of each column for each segment
    - Fit kde for numeric
    - Get frequency distribution for categorical
4. Output all distribution for each segment

Used in ABM_modeling.py

"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data_processing.log"), logging.StreamHandler()],
)
logger = logging.getLogger("data_processor")
logger.propagate = False  # Ensure logs from this file are captured


class DistributionAnalyzer:

    def __init__(self, data: pd.DataFrame):
        """
        Initialize with customer data.

        Args:
            data: DataFrame containing customer data
        """
        self.data = data
        self.kde_cluster_cols: Dict[int, Dict[str, gaussian_kde]] = defaultdict(
            dict
        )  # {1: {'rating': {kernel:gaussian, pdf_values:...},...},...}
        self.cat_dist_cluster_cols: Dict[int, Dict[str, Dict[str, float]]] = (
            defaultdict(lambda: defaultdict(dict))
        )  # {1: {'occupation': {1: 0.25, 2:0.27,...,10:0.18},...},...}
        self.cat_cols = []
        self.num_cols = []
        self.id_cols = []
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            "DistributionAnalyzer initialized with data shape: %s", data.shape
        )

    def _is_date(self, value: str) -> bool:
        """Check if a string can be parsed as a date."""
        try:
            parse(value, fuzzy=True)
            return True
        except (ValueError, TypeError):
            return False

    def process_dataset(
        self, cutoff: float = 50, id_list: list[str] = ["sku", "id"]
    ) -> pd.DataFrame:
        """
        Identify column types.
        Process categorical columns with one hot encoding.
        Prepare for clustering with KMeans.

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
        text_cols: list[str] = []

        for i in self.data.columns:
            col = str(i).lower()
            id = False

            # Check for ID columns
            if any(word in col for word in id_list) or self.data[i].nunique() == len(
                self.data
            ):
                id_cols.append(i)
                id = True
                self.logger.debug("Identified ID column: %s", i)

            if id:
                continue

            # Check for datetime columns
            if self.data[i].dtype == "object":
                sample_size = min(100, len(self.data[i]))
                date_count = sum(
                    self._is_date(str(x)) for x in self.data[i].head(sample_size)
                )
                if date_count / sample_size > 0.9:  # If 80% of samples are dates
                    if "-" in self.data[i][0]:
                        datetime_cols.append(i)
                        self.logger.debug("Added datetime column: %s", i)

                    else:
                        cat_cols.append(i)
                        self.logger.debug(
                            "Added single datetime column as categorical: %s", i
                        )
                    continue

            # Check for categorical, numerical or text columns
            if self.data[i].nunique() <= cutoff:
                cat_cols.append(i)
                self.logger.debug("Added categorical column: %s", i)
            elif pd.api.types.is_numeric_dtype(self.data[i]):
                num_cols.append(i)
                self.logger.debug("Added numerical column: %s", i)
            else:
                text_cols.append(i)
                self.logger.debug("Added text column: %s", col)

        self.logger.info(
            "Found: \n %s as categorical columns, \n %s as numerical columns, \n %s as ID columns, \n %s as datetime columns, \n %s as text columns",
            cat_cols,
            num_cols,
            id_cols,
            datetime_cols,
            text_cols,
        )

        assert len(cat_cols + num_cols + id_cols + datetime_cols + text_cols) == len(
            self.data.columns
        ), f"Some columns are missing. Original: {len(self.data.columns)}, Final: {len(cat_cols+num_cols+id_cols+datetime_cols+text_cols)}"

        # Splitting the datetime columns into categorical components
        for col in datetime_cols:
            try:
                self.data[["year", "month", "date"]] = self.data[col].str.split(
                    "-", expand=True
                )
                cat_cols.append("date")
                cat_cols.append("month")
                cat_cols.append("year")
            except:
                self.logger.error(
                    "Error splitting wrong format: %s", self.data[col].head(1)
                )
                raise

            self.data.drop(columns=col, axis=1, inplace=True)

        self.text_cols = text_cols
        self.cat_cols = cat_cols
        self.num_cols = num_cols
        self.id_cols = id_cols

        self.logger.info(
            "Final columns: \n %s as categorical columns, \n %s as numerical columns, \n %s as ID columns, \n %s as text columns",
            self.cat_cols,
            self.num_cols,
            self.id_cols,
            self.text_cols,
        )

        # One-hot encode categorical columns
        encoded_df = pd.get_dummies(self.data, columns=cat_cols, dtype=int)
        return encoded_df

    def cluster_data_kmeans(
        self,
        encoded_df: pd.DataFrame,
        n_clusters: int = 5,
        drop_columns: list[str] = [],
    ) -> pd.DataFrame:
        """
        Cluster the data using KMeans. Maybe can change to other clustering methods.

        22/9 Update: Had to lower clusters from 15->5 to optimize memory usage in production.
        """
        drop_columns = drop_columns + self.id_cols + self.text_cols
        existing_columns = [col for col in drop_columns if col in encoded_df.columns]
        if existing_columns:
            encoded_df = encoded_df.drop(columns=existing_columns, axis=1)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(encoded_df)
        encoded_df["cluster"] = kmeans.labels_

        return encoded_df

    def fit_kde(
        self,
        column: str,
        cluster_df: pd.DataFrame,
        cluster_num: int,
        plot: bool = False,
    ) -> gaussian_kde:
        """
        Fit a Kernel Density Estimation model to a specific column.

        Args:
            column: Name of the column to analyze
            bandwidth: Bandwidth for KDE (if None, use Scott's rule)
            plot: Whether to generate visualization

        Returns:
            Fitted KDE model
        """

        data = np.array(cluster_df[column].dropna().values)
        kde = gaussian_kde(data)
        self.kde_cluster_cols[cluster_num][column] = kde
        self.logger.debug("KDE fitted successfully for column %s", column)

        if plot:
            self._plot_kde(data, kde, column)

        return kde

    def _plot_kde(self, data: np.ndarray, kde: gaussian_kde, column: str):
        """
        Plot the data histogram and KDE estimate.

        Args:
            data: Data array
            kde: Fitted KDE model
            column: Column name for title
        """
        plt.figure(figsize=(10, 6))

        # Create histogram
        plt.hist(data, bins=30, density=True, alpha=0.6, label="Data")

        # Generate KDE estimate
        x = np.linspace(data.min(), data.max(), 200)
        pdf_kde = kde(x)

        # Plot KDE
        plt.plot(x, pdf_kde, label="Kernel Density Estimate")

        plt.title(f"Kernel Density Estimation - {column}")
        plt.legend()
        plt.grid(True)
        plt.show()

    def get_frequency_distribution(self, cluster_df: pd.DataFrame, cluster_num: int):
        """
        Get the frequency distribution of a categorical column.
        """
        self.logger.info(
            "Getting all categorical distribution for cluster %d", cluster_num
        )
        # Getting only the categorical cols
        cat_only_df = cluster_df.drop(columns=self.num_cols, axis=1)
        cat_dist = cat_only_df.sum() / len(cat_only_df)

        # Getting the dist of each column
        for col in self.cat_cols:
            dist = cat_dist[cat_dist.index.str.contains(col)]

            for index, value in dist.items():
                categories = str(index).split("_")[-1]
                self.cat_dist_cluster_cols[cluster_num][col][categories] = value
        return self.cat_dist_cluster_cols

    def analyze_segments_col_dist(self, encoded_df: pd.DataFrame):
        """
        Analyze distributions of categorical and numerical columns for each customer.

        Args:
            encoded_df: Encoded dataframe with cluster labels
        """
        unique_clusters = encoded_df["cluster"].unique()
        cluster_all_dist = defaultdict(list)

        for num in unique_clusters:
            cluster_df = encoded_df[encoded_df["cluster"] == num]

            if len(cluster_df) <= 2:
                self.logger.info("Cluster %d has less than 2 samples. Skipping...", num)
                continue
            else:
                self.logger.info(
                    "Analyzing cluster %d with %d samples", num, len(cluster_df)
                )

            cluster_all_dist[num].append(len(cluster_df) / len(encoded_df))
            # Getting cat dist
            self.get_frequency_distribution(cluster_df, num)  # pyright: ignore
            cluster_all_dist[num].append(self.cat_dist_cluster_cols[num])
            # Getting num dist
            for col in self.num_cols:
                self.fit_kde(col, cluster_df, num)  # pyright: ignore

            cluster_all_dist[num].append(self.kde_cluster_cols[num])

        return cluster_all_dist

    def generate_synthetic_data(
        self, cluster_prob: Dict[int, float], size: int = 1000
    ) -> pd.DataFrame:
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
        columns = np.array(self.cat_cols + self.num_cols)

        for _ in range(size):
            cluster_id = np.random.choice(
                list(cluster_prob.keys()), p=list(cluster_prob.values())
            )

            # Categorical
            cat_dist = self.cat_dist_cluster_cols[cluster_id]
            cat_values = []
            for col in self.cat_cols:
                dist = cat_dist[col]
                cat = list(dist.keys())
                prob = list(dist.values())
                sample = np.random.choice(cat, p=prob)
                cat_values.append(sample)

            # Numerical
            num_values = []
            for col in self.num_cols:
                kde = self.kde_cluster_cols[cluster_id][col]
                samples = kde.resample(1)
                num_values.append(samples)

            synthetic_data.append(cat_values + num_values)

        return pd.DataFrame(synthetic_data, columns=columns)


def get_dataset_distribution(data_file_path: str, max_rows=10000):
    """
    Get the distribution of a dataset.
    """
    # Configure logging for main
    logger = logging.getLogger(__name__)
    logger.info("Starting data processing pipeline")

    try:
        # Read data from csv
        name = data_file_path.split("/")[-1]

        with open(data_file_path, "r") as f:
            total_rows = sum(1 for _ in f) - 1  # For header

        if total_rows > max_rows:
            random_rows_skip = sorted(
                random.sample(range(1, total_rows), total_rows - max_rows)
            )
            data = pd.read_csv(data_file_path, index_col=0, skiprows=random_rows_skip)
            logger.info(
                f"Data from {name} loaded successfully with {max_rows} row limit."
            )
        else:
            data = pd.read_csv(data_file_path, index_col=0)
            logger.info(f"Data from {name} loaded successfully for entire file.")

        # Initialize processor
        processor = DistributionAnalyzer(data)
        processed_data = processor.process_dataset()
        logger.info(f"Categorical data processing completed for {name}")

        cluster_data = processor.cluster_data_kmeans(processed_data)
        logger.info(
            f"Clustering completed. Found {len(cluster_data['cluster'].unique())} clusters for {name}"
        )

        all_cluster_dist = processor.analyze_segments_col_dist(cluster_data)
        logger.info(f"Customer segment analysis completed for {name}")

        return all_cluster_dist

    except Exception as e:
        logger.error("Error in data processing pipeline: %s", str(e), exc_info=True)
        raise

    # with open(f'/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/method/result.json', 'w') as f:
    #     json.dump(final_analysis_results, f, indent=4)
