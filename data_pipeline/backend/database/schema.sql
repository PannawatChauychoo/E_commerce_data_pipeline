-- Create schema for Walmart simulation data

DROP SCHEMA IF EXISTS walmart CASCADE;
CREATE SCHEMA IF NOT EXISTS walmart;

-- Customer Type 1 (Walmart Customer) demographics
CREATE TABLE walmart.cust1_demographics (
    unique_id INTEGER PRIMARY KEY NOT NULL,
    age INT,
    gender VARCHAR(10),
    city_category VARCHAR(20),
    stay_in_current_city_years VARCHAR(10),
    marital_status VARCHAR(10),
    segment_id INTEGER,
    visit_prob FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Type 2 (E-commerce) demographics
CREATE TABLE walmart.cust2_demographics (
    unique_id INTEGER PRIMARY KEY NOT NULL,
    branch VARCHAR(50),
    city VARCHAR(50),
    customer_type VARCHAR(20),
    gender VARCHAR(10),
    payment_method VARCHAR(20),
    segment_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE walmart.products (
    product_id INTEGER PRIMARY KEY NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price FLOAT NOT NULL,
    stock INTEGER,
    lead_days INTEGER,
    ordering_cost FLOAT,
    holding_cost_per_unit FLOAT,
    EOQ FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE walmart.customers_lookup (
    customer_id SERIAL PRIMARY KEY,
    external_id INTEGER NOT NULL,
    cust_type VARCHAR(10) NOT NULL,
    segment_id INTEGER,
    UNIQUE (external_id, cust_type, segment_id)
);

-- Combined transactions table for both customer types
CREATE TABLE walmart.transactions (
    transaction_id SERIAL PRIMARY KEY,
    unique_id INTEGER references walmart.customers_lookup(customer_id),
    product_id INTEGER references walmart.products(product_id),
    unit_price FLOAT,
    quantity INTEGER,
    date_purchased DATE,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_category ON walmart.transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_product ON walmart.transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON walmart.transactions(unique_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON walmart.transactions(date_purchased);
