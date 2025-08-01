import csv

PRODUCT_TAXONOMY = {
    'Food & Beverages': {
        'Fresh Food': {
            'Produce': {},
            'Meat & Seafood': {},
            'Dairy & Eggs': {},
            'Bakery': {},
        },
        'Packaged Food': {
            'Pantry': {},
            'Snacks': {},
            'Beverages': {},
            'Prepared Foods': {}
        }
    },
    'Home & Living': {
        'Home': {},
        'Home Improvement': {},
        'Household Essentials': {},
        'Patio & Garden': {},
        'Arts, Crafts & Sewing': {}
    },
    'Health & Beauty': {
        'Beauty': {},
        'Premium Beauty': {},
        'Personal Care': {},
        'Health and Medicine': {}
    },
    'Fashion': {
        'Clothing': {},
        'Jewelry': {},
        'Fashion Accessories': {}
    },
    'Electronics': {
        'Electronic Accessories': {}
    },
    'Toys & Entertainment': {
        'Toys': {},
        'Collectibles': {},
        'Party & Occasions': {}
    },
    'Special Categories': {
        'Baby': {},
        'Pets': {},
        'Auto & Tires': {},
        'Seasonal': {},
        'Shop with Purpose': {},
        'Subscriptions': {},
        'Sports & Outdoors': {}
    }
}

CATEGORY_SOURCES = {
    'Product': [
        'Beauty', 'Home', 'Clothing', 'Sports & Outdoors', 'Food', 'Jewelry',
        'Personal Care', 'Patio & Garden', 'Health and Medicine', 'Pets',
        'Premium Beauty', 'Baby', 'Household Essentials', 'Home Improvement',
        'Shop with Purpose', 'Party & Occasions', 'Electronics', 'Collectibles',
        'Arts, Crafts & Sewing', 'Subscriptions', 'Toys', 'Seasonal', 'Auto & Tires'
    ],
    'Commerce': [
        'Health and beauty', 'Electronic accessories', 'Home and lifestyle',
        'Sports and travel', 'Food and beverages', 'Fashion accessories'
    ],
    'Customer': [
        'Meat & Seafood', 'Produce', 'Bakery', 'Non-Food Items', 'Dairy & Eggs',
        'Beverages', 'Snacks', 'Prepared Foods'
    ],
    'Transaction': [
        'Beverages', 'Meat & Seafood', 'Pantry', 'Dairy & Eggs', 'Non-Food Items',
        'Snacks', 'Produce', 'Prepared Foods', 'Uncategorized', 'Bakery'
    ]
}

def get_source_table(category_name):
    for source, categories in CATEGORY_SOURCES.items():
        categories = [i.lower() for i in categories]
        if category_name.lower() in categories:
            return source
    return 'Surrogate'

def write_taxonomy_to_csv(taxonomy, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['cat_id', 'parent_id', 'level', 'cat_name', 'path'])

        def traverse(node, parent_id, level, path):
            # Recursively traverses the taxonomy tree and writes each category to CSV
            # For each category (key) and its subcategories (value) in the current node:
            for i, (key, value) in enumerate(node.items(), start=1):
                # Create category ID by appending index to parent ID (e.g. "1-2-3")
                cat_id = f"{parent_id}-{i}" if parent_id else str(i)
                # Build full path (e.g. "Food > Beverages > Wine") 
                current_path = f"{path} > {key}" if path else key
                # Write category info to CSV: ID, parent, level, name, full path
                writer.writerow([cat_id, parent_id or '-', level, key, current_path])
                # Recursively process subcategories, incrementing level
                traverse(value, cat_id, level + 1, current_path)

        traverse(taxonomy, None, 1, '')

def write_category_mapping_to_csv(taxonomy, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['source_table', 'raw_category_label', 'cat_id'])

        def traverse(node, parent_id, level, path):
            for i, (key, value) in enumerate(node.items(), start=1):
                cat_id = f"{parent_id}-{i}" if parent_id else str(i)
                source_table = get_source_table(key)
                writer.writerow([source_table, key, cat_id])
                traverse(value, cat_id, level + 1, path)

        traverse(taxonomy, None, 1, '')

write_taxonomy_to_csv(PRODUCT_TAXONOMY, '/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/product_taxonomy.csv')
write_category_mapping_to_csv(PRODUCT_TAXONOMY, '/Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/data_source/category_mapping.csv') 