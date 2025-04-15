import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import gaussian_kde, norm
import pickle
    
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
"""


def create_product_price_table():
    # Read mapping files
    category_mapping = pd.read_csv('data_source/category_mapping.csv')
    product_taxonomy = pd.read_csv('data_source/product_taxonomy.csv')
    
    # Read product data
    walmart_products = pd.read_csv('data_source/Walmart_products.csv')
    walmart_commerce = pd.read_csv('data_source/Walmart_commerce.csv')
    
    # Read transaction data in chunks
    chunksize = 100000
    transaction_chunks = []
    try:
        for chunk in pd.read_csv('data_source/Walmart_transactions.csv', chunksize=chunksize, index_col=0):
            available_cols = chunk.columns.tolist()
            print("Available columns in transaction data:", available_cols)
            
            category_col = next((col for col in available_cols if 'category' in col.lower()), None)
            price_col = next((col for col in available_cols if 'price' in col.lower() or 'unit' in col.lower()), None)
            quantity_col = next((col for col in available_cols if 'quantity' in col.lower()), None)
            
            if category_col and price_col and quantity_col:
                transaction_chunks.append(chunk[[category_col, price_col, quantity_col]])
            else:
                print("Warning: Could not find required columns in chunk")
                continue
                
        walmart_transactions = pd.concat(transaction_chunks, ignore_index=True)
    except Exception as e:
        print(f"Error processing transaction data: {str(e)}")
        walmart_transactions = pd.DataFrame(columns=['category', 'unit_price', 'quantity'])
    
    # Create mapping dictionaries
    category_to_id = dict(zip(category_mapping['raw_category_label'], category_mapping['cat_id']))
    id_to_path = dict(zip(product_taxonomy['cat_id'], product_taxonomy['path']))
    
    # Process Walmart products data
    products_df = walmart_products[['categories', 'final_price']].copy()
    products_df['category_id'] = products_df['categories'].map(category_to_id)
    products_df['category_path'] = products_df['category_id'].map(id_to_path)
    products_df = products_df.rename(columns={'final_price': 'unit_price'})
    products_df['quantity'] = 1  # Default quantity for products
    
    # Process Walmart commerce data
    commerce_df = walmart_commerce[['product_line', 'unit_price', 'quantity']].copy()
    commerce_df['category_id'] = commerce_df['product_line'].map(category_to_id)
    commerce_df['category_path'] = commerce_df['category_id'].map(id_to_path)
    
    # Process Walmart transactions data if available
    if not walmart_transactions.empty:
        transactions_df = walmart_transactions.copy()
        transactions_df = transactions_df.rename(columns={
            transactions_df.columns[0]: 'category',
            transactions_df.columns[1]: 'unit_price',
            transactions_df.columns[2]: 'quantity'
        })
        
        transactions_df['category_id'] = transactions_df['category'].map(category_to_id)
        transactions_df['category_path'] = transactions_df['category_id'].map(id_to_path)
        
        # Combine all dataframes
        combined_df = pd.concat([
            products_df[['category_path', 'unit_price', 'quantity']],
            commerce_df[['category_path', 'unit_price', 'quantity']],
            transactions_df[['category_path', 'unit_price', 'quantity']]
        ], ignore_index=True)
    else:
        combined_df = pd.concat([
            products_df[['category_path', 'unit_price', 'quantity']],
            commerce_df[['category_path', 'unit_price', 'quantity']]
        ], ignore_index=True)
    
    # Calculate statistics per category
    price_table = combined_df.groupby('category_path').agg({
        'unit_price': ['mean', 'min', 'max', 'std', 'count'],
        'quantity': ['mean', 'min', 'max', 'std', 'count']
    }).reset_index()
    
    # Flatten multi-index columns
    price_table.columns = [
        'category_path', 
        'avg_unit_price', 'min_price', 'max_price', 'std_price', 'price_count',
        'avg_quantity', 'min_quantity', 'max_quantity', 'std_quantity', 'quantity_count'
    ]
    
    # Create KDE distributions for each category
    kde_distributions = {}
    for category in combined_df['category_path'].unique():
        category_data = combined_df[combined_df['category_path'] == category]
        
        # Price distribution
        price_data = category_data['unit_price'].dropna()
        if len(price_data) >= 5:  # Minimum 5 points for KDE
            try:
                price_kde = gaussian_kde(price_data)
                price_dist_type = 'kde'
            except:
                # Fallback to normal distribution if KDE fails
                mean = price_data.mean() if price_data.mean() > 0 else 1  # Ensure positive mean
                std = max(price_data.std(), 0.1)    # Ensure positive std
                price_kde = norm(loc=mean, scale=std)
                price_dist_type = 'normal'
        else:
            # Use normal distribution for very small samples
            mean = price_data.mean() if price_data.mean() > 0 else 1  # Ensure positive mean
            std = max(price_data.std(), 0.1)    # Ensure positive std
            price_kde = norm(loc=mean, scale=std)
            price_dist_type = 'normal'
        
        # Quantity distribution
        quantity_data = category_data['quantity'].dropna()
        if len(quantity_data) >= 5:  # Minimum 5 points for KDE
            try:
                quantity_kde = gaussian_kde(quantity_data)
                quantity_dist_type = 'kde'
            except:
                # Fallback to normal distribution if KDE fails
                mean = max(quantity_data.mean(), 1)  # Ensure positive mean
                std = max(quantity_data.std(), 1)    # Ensure positive std
                quantity_kde = norm(loc=mean, scale=std)
                quantity_dist_type = 'normal'
        else:
            # Use normal distribution for very small samples
            mean = max(quantity_data.mean(), 1)  # Ensure positive mean
            std = max(quantity_data.std(), 1)    # Ensure positive std
            quantity_kde = norm(loc=mean, scale=std)
            quantity_dist_type = 'normal'
        
        kde_distributions[category] = {
            'price_kde': price_kde,
            'quantity_kde': quantity_kde,
            'price_dist_type': price_dist_type,
            'quantity_dist_type': quantity_dist_type,
            'price_data': price_data.values,
            'quantity_data': quantity_data.values
        }
    
    # Save KDE distributions
    with open('data_source/category_kde_distributions.pkl', 'wb') as f:
        pickle.dump(kde_distributions, f)
    
    # Save to CSV
    price_table.to_csv('data_source/product_price_table.csv', index=False)
    return price_table, kde_distributions

if __name__ == "__main__":
    price_table, kde_distributions = create_product_price_table()
    print("Product price table and KDE distributions created successfully!")
    print("\nSample of the price table:")
    print(price_table.head()) 