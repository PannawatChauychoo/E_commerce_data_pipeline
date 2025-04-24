-- Create schema for Walmart simulation data
CREATE SCHEMA walmart;

-- Set search path
SET search_path TO walmart;

-- Customer Type 1 (Walmart Customer) demographics
CREATE TABLE cust1_demographics (
    unique_id INTEGER PRIMARY KEY NOT NULL,
    age VARCHAR(10),
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
CREATE TABLE cust2_demographics (
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

CREATE TABLE products (
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

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    external_id INTEGER NOT NULL,
    cust_type VARCHAR(10) NOT NULL,
    UNIQUE (external_id, cust_type)
);

-- Combined transactions table for both customer types
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    unique_id INTEGER references customers(customer_id),
    product_id INTEGER references products(product_id),
    unit_price FLOAT,
    quantity INTEGER,
    date_purchased DATE,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_product ON transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(unique_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date_purchased);
