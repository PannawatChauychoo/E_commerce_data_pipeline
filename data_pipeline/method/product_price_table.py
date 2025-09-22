# type: ignore
from pathlib import Path

import numpy as np
import pandas as pd
from fuzzywuzzy import process
from scipy.stats import gaussian_kde, norm

"""
This code creates a product price table by:

1. Reading source data files:
   - category_mapping.csv: Maps raw category labels to category IDs
   - product_taxonomy.csv: Maps category IDs to full category paths
   - Walmart product/commerce/transaction data files

2. Processing transaction data in chunks to handle large files:
   - Reads CSV in 100k row chunks
   - Extracts category and price columns
   - Concatenates chunks into single DataFrame

3. Creating mapping dictionaries:
   - category_to_id: Raw category label → category ID
   - id_to_path: Category ID → full category path 

4. Transforming product data:
   - Maps categories to standardized IDs and paths
   - Renames price columns for consistency

5. Processing commerce data similarly:
   - Maps product lines to category IDs and paths
   - Preserves unit price information

Potential causes for bugs:
- There is a nan category in the output
- Categories with only one product are included in the output

Solutions
- Drop NaN categories (Doesn't work)
- Create random quantity between 1 and 100 for products data (Remove too many categories)
- Getting the average quantity, quantity std from the average of the category (Done)
- Use fuzzy matching to map raw categories to product_taxonomy (Done)
"""


def read_and_process_transaction_data(
    file_path: str, chunksize: int = 100000
) -> pd.DataFrame:
    """
    Reads and processes transaction data in chunks to handle large files efficiently.

    Args:
        file_path (str): Path to the transaction data CSV file
        chunksize (int): Number of rows to read per chunk

    Returns:
        pd.DataFrame: Processed transaction data with category, price, and quantity columns
    """
    transaction_chunks = []
    try:
        for chunk in pd.read_csv(file_path, chunksize=chunksize, index_col=0):
            available_cols = chunk.columns.tolist()

            category_col = next(
                (col for col in available_cols if "category" in col.lower()), None
            )
            price_col = next(
                (
                    col
                    for col in available_cols
                    if "price" in col.lower() or "unit" in col.lower()
                ),
                None,
            )
            quantity_col = next(
                (col for col in available_cols if "quantity" in col.lower()), None
            )

            if category_col and price_col and quantity_col:
                transaction_chunks.append(
                    chunk[[category_col, price_col, quantity_col]]
                )
            else:
                print("Warning: Could not find required columns in chunk")
                continue

        return pd.concat(transaction_chunks, ignore_index=True)
    except Exception as e:
        print(f"Error processing transaction data: {str(e)}")
        return pd.DataFrame(columns=np.array(["category", "unit_price", "quantity"]))


def create_mapping_dictionaries(
    category_mapping: pd.DataFrame, product_taxonomy: pd.DataFrame
) -> tuple:
    """
    Creates mapping dictionaries for category IDs and paths.

    Args:
        category_mapping (pd.DataFrame): DataFrame containing category mapping data
        product_taxonomy (pd.DataFrame): DataFrame containing product taxonomy data

    Returns:
        tuple: (category_to_id, id_to_path) mapping dictionaries
    """
    category_to_id = dict(
        zip(category_mapping["raw_category_label"], category_mapping["cat_id"])
    )
    id_to_path = dict(zip(product_taxonomy["cat_id"], product_taxonomy["path"]))
    return category_to_id, id_to_path


def get_category_id(x, category_to_id):
    """
    Use fuzzy string matching to map product lines to category IDs
    """
    if not x:
        return None
    match = process.extractOne(x, category_to_id.keys())
    return category_to_id[match[0]] if match else None


def process_product_data(
    products_df: pd.DataFrame, category_to_id: dict, id_to_path: dict
) -> pd.DataFrame:
    """
    Processes product data by adding random quantities and mapping categories.

    Args:
        products_df (pd.DataFrame): Raw product data
        category_to_id (dict): Mapping from category labels to IDs
        id_to_path (dict): Mapping from category IDs to full paths

    Returns:
        pd.DataFrame: Processed product data with mapped categories and random quantities
    """
    processed_df = products_df[["categories", "final_price"]].copy()
    processed_df["quantity"] = np.random.randint(1, 100, size=len(processed_df))
    processed_df["category_id"] = processed_df["categories"].apply(
        get_category_id, category_to_id=category_to_id
    )
    processed_df["category_path"] = processed_df["category_id"].map(id_to_path)
    return processed_df.rename(columns={"final_price": "unit_price"})


def process_commerce_data(
    commerce_df: pd.DataFrame, category_to_id: dict, id_to_path: dict
) -> pd.DataFrame:
    """
    Processes commerce data by mapping product lines to categories.

    Args:
        commerce_df (pd.DataFrame): Raw commerce data
        category_to_id (dict): Mapping from category labels to IDs
        id_to_path (dict): Mapping from category IDs to full paths

    Returns:
        pd.DataFrame: Processed commerce data with mapped categories
    """
    processed_df = commerce_df[["product_line", "unit_price", "quantity"]].copy()
    processed_df["category_id"] = processed_df["product_line"].apply(
        get_category_id, category_to_id=category_to_id
    )
    processed_df["category_path"] = processed_df["category_id"].map(id_to_path)
    return processed_df


def process_transaction_data(
    transactions_df: pd.DataFrame, category_to_id: dict, id_to_path: dict
) -> pd.DataFrame:
    """
    Processes transaction data by mapping categories and adding random quantities where needed.

    Args:
        transactions_df (pd.DataFrame): Raw transaction data
        category_to_id (dict): Mapping from category labels to IDs
        id_to_path (dict): Mapping from category IDs to full paths

    Returns:
        pd.DataFrame: Processed transaction data with mapped categories and quantities
    """
    processed_df = transactions_df.copy()
    processed_df = processed_df.rename(
        columns={
            processed_df.columns[0]: "category",
            processed_df.columns[1]: "unit_price",
            processed_df.columns[2]: "quantity",
        }
    )

    processed_df["category_id"] = processed_df["category"].map(category_to_id)
    processed_df["category_path"] = processed_df["category_id"].map(id_to_path)

    # mask = processed_df['quantity'] == 1
    # processed_df.loc[mask, 'quantity'] = np.random.randint(1, 100, size=mask.sum())

    return processed_df


def extract_distribution_types(combined_df: pd.DataFrame) -> dict:
    """
    Label distributions type for price and quantity for each category.
    Easier to save as numpy array and load distribution when loading.
    - If <5 samples => normal label with mean = 1 & std = 0.01
    - if >=5 samples => kde label

    Args:
        combined_df (pd.DataFrame): Combined data from all sources

    Returns:
        dict: Dictionary containing KDE distributions for each category
    """
    kde_distributions = {}
    # Drop rows with NaN category_path before getting unique categories
    valid_categories = combined_df["category_path"].dropna().unique()

    for category in valid_categories:
        category_data = combined_df[combined_df["category_path"] == category]

        # Price distribution
        price_data = category_data["unit_price"].dropna().values
        if len(price_data) >= 5:
            price_dist_type = "kde"
            price_mean = None
            price_std = None
        else:
            price_dist_type = "normal"
            price_mean = float(price_data.mean()) if price_data.size else 1.0
            price_std = float(price_data.std()) if price_data.size else 0.01

        # Quantity distribution
        quantity_data = category_data["quantity"].dropna().values
        if len(quantity_data) >= 5:
            quantity_dist_type = "kde"
            quantity_mean = None
            quantity_std = None
        else:
            quantity_dist_type = "normal"
            quantity_mean = float(quantity_data.mean()) if quantity_data.size else 1.0
            quantity_std = float(quantity_data.std()) if quantity_data.size else 0.01

        kde_distributions[category] = {
            "price_data": price_data,
            "price_dist_type": price_dist_type,
            "price_mean": price_mean,
            "price_std": price_std,
            "quantity_data": quantity_data,
            "quantity_dist_type": quantity_dist_type,
            "quantity_mean": quantity_mean,
            "quantity_std": quantity_std,
        }

    return kde_distributions


def save_distributions_to_npz(kde_dict: dict, out_path: str | Path):
    """
    Write a single .npz file containing:
      - raw price_data / quantity_data arrays
      - a small “dist_type” label per category
    so that you can reconstruct a GaussianKDE or Normal later.
    """

    out = Path(out_path).with_suffix(".npz")
    container = {}

    for category, obj in kde_dict.items():
        prefix = f"{category}__"

        # 1) Always save the raw arrays:
        container[prefix + "price_data"] = obj["price_data"]
        container[prefix + "quantity_data"] = obj["quantity_data"]

        # 2) Save dist_type as a 0-dim string array:
        container[prefix + "price_dist_type"] = np.array(
            obj["price_dist_type"], dtype="U10"
        )
        container[prefix + "quantity_dist_type"] = np.array(
            obj["quantity_dist_type"], dtype="U10"
        )

    np.savez_compressed(out, **container)
    print(f"Saved distributions → {out}")


def load_distributions_from_file(npz_path: str | Path) -> dict:
    """
    Load exactly one .npz file of KDE/normal data and rebuild the distributions.

    Args:
        npz_path: path to a file like "category_kde_distributions.npz"

    Returns:
        A dict mapping each category → {
            "price_kde":   <gaussian_kde or norm>,
            "quantity_kde":<gaussian_kde or norm>,
            "price_dist_type":    str,
            "quantity_dist_type": str,
            "price_data":    np.ndarray,
            "quantity_data": np.ndarray
        }
    """
    npz_file = Path(npz_path)
    if not npz_file.exists():
        raise FileNotFoundError(f"No file found at {npz_file}")

    archive = np.load(npz_file, allow_pickle=False)
    result = {}

    # Extract the set of category prefixes from the keys, e.g. "electronics__price_data"
    prefixes = {key.split("__")[0] for key in archive.keys()}

    for category in prefixes:
        prefix = f"{category}__"

        # 1) load raw arrays
        price_data = archive[prefix + "price_data"]
        quantity_data = archive[prefix + "quantity_data"]

        # 2) load dist_type labels (0-d arrays of string)
        price_dist_type = str(archive[prefix + "price_dist_type"])
        quantity_dist_type = str(archive[prefix + "quantity_dist_type"])

        # 3) rebuild the price distribution
        if price_dist_type == "kde":
            price_kde = gaussian_kde(price_data)
        else:  # "normal"
            μ = float(price_data.mean()) or 1.0
            σ = float(price_data.std()) or 0.01
            price_kde = norm(loc=μ, scale=max(σ, 0.01))

        # 4) rebuild the quantity distribution
        if quantity_dist_type == "kde":
            quantity_kde = gaussian_kde(quantity_data)
        else:
            μq = float(quantity_data.mean()) or 1.0
            σq = float(quantity_data.std()) or 0.01
            quantity_kde = norm(loc=μq, scale=max(σq, 0.01))

        # 5) assemble the same dict‐structure you used before
        result[category] = {
            "price_kde": price_kde,
            "quantity_kde": quantity_kde,
            "price_dist_type": price_dist_type,
            "quantity_dist_type": quantity_dist_type,
            "price_data": price_data,
            "quantity_data": quantity_data,
        }

    return result


def create_product_price_table():
    """
    Creates a comprehensive product price table by:
    1. Reading and processing data from multiple sources
    2. Creating category mappings between datasets
    3. Processing columns in product, commerce, and transaction dataset
    4. Save distribution spec for price and quantity into npz file
    5. Create and save price table as csv
    """
    wd = str(Path(__file__).parent)  # Setting the parent directory for consistency

    # Read mapping files
    category_mapping = pd.read_csv(wd + "/../data_source/category_mapping.csv")
    product_taxonomy = pd.read_csv(wd + "/../data_source/product_taxonomy.csv")

    # Read product data
    walmart_products = pd.read_csv(wd + "/../data_source/Walmart_products.csv")
    walmart_commerce = pd.read_csv(wd + "/../data_source/Walmart_commerce.csv")

    # Process transaction data
    walmart_transactions = read_and_process_transaction_data(
        wd + "/../data_source/Walmart_transactions.csv"
    )

    # Create mapping dictionaries
    category_to_id, id_to_path = create_mapping_dictionaries(
        category_mapping, product_taxonomy
    )

    # Process data from different sources
    products_df = process_product_data(walmart_products, category_to_id, id_to_path)
    commerce_df = process_commerce_data(walmart_commerce, category_to_id, id_to_path)

    # Combine data
    if not walmart_transactions.empty:
        transactions_df = process_transaction_data(
            walmart_transactions, category_to_id, id_to_path
        )
        combined_df = pd.concat(
            [
                products_df[["category_path", "unit_price", "quantity"]],
                commerce_df[["category_path", "unit_price", "quantity"]],
                transactions_df[["category_path", "unit_price", "quantity"]],
            ],
            ignore_index=True,
        )
    else:
        combined_df = pd.concat(
            [
                products_df[["category_path", "unit_price", "quantity"]],
                commerce_df[["category_path", "unit_price", "quantity"]],
            ],
            ignore_index=True,
        )

    # Create KDE distributions
    distribution_specs = extract_distribution_types(combined_df)

    # Save distribution results
    save_distributions_to_npz(
        distribution_specs, wd + "/../data_source/category_distributions"
    )

    print("specs save successfully at ../data_source/category_distributions.npz")

    """ 
    -------- Creating the price table csv file -------- 
    """
    # Filter out main categories first
    combined_df = combined_df[combined_df["category_path"].str.contains(">", na=False)]

    price_table = (
        combined_df.groupby("category_path")
        .agg({"unit_price": ["mean", "std"], "quantity": ["mean", "std", "count"]})
        .reset_index()
    )

    # Flatten multi-index columns
    price_table.columns = [
        "category_path",
        "avg_unit_price",
        "std_price",
        "avg_quantity",
        "std_quantity",
        "quantity_count",
    ]

    # Trying to give categories with only one sample their parent's category avg
    main_categories = price_table["category_path"].str.split(" > ").str[0].unique()

    for cat in main_categories:
        cat_mask = price_table["category_path"].str.startswith(cat)
        cat_group = price_table[cat_mask]

        # Calculate group averages
        group_avgs = {
            "avg_quantity": cat_group["quantity_count"].mean(),
            "std_quantity": cat_group["std_quantity"].mean(),
            "avg_unit_price": cat_group["avg_unit_price"].mean(),
            "std_price": (cat_group["avg_unit_price"] / cat_group["std_price"]).mean(),
        }

        # Update single count categories with group averages
        single_count_mask = cat_group["quantity_count"] == 1
        for col, avg in group_avgs.items():
            price_table.loc[cat_mask & single_count_mask, col] = avg

    # Save price table
    # Double check to ensure no main categories
    price_table = price_table[price_table["category_path"].str.contains(">", na=False)]
    price_table.to_csv(wd + "/../data_source/product_price_table.csv", index=False)
    return price_table


if __name__ == "__main__":
    price_table = create_product_price_table()
    print("Product price table and distribution file created successfully!")
    print("\nSample of the price table:")
    print(price_table.head())
