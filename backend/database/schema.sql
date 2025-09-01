-- Create schema for Walmart simulation data
CREATE SCHEMA IF NOT EXISTS walmart;

-- Customer Type 1 (Walmart Customer) demographics
CREATE TABLE IF NOT EXISTS walmart.cust1 (
    unique_id INTEGER PRIMARY KEY NOT NULL,
    age INT,
    gender VARCHAR(10),
    city_category VARCHAR(20),
    stay_in_current_city_years VARCHAR(10),
    marital_status VARCHAR(10),
    segment_id INTEGER,
    visit_prob FLOAT,
    run_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Type 2 (E-commerce) demographics
CREATE TABLE IF NOT EXISTS walmart.cust2 (
    unique_id INTEGER PRIMARY KEY NOT NULL,
    branch VARCHAR(50),
    city VARCHAR(50),
    customer_type VARCHAR(20),
    gender VARCHAR(10),
    payment_method VARCHAR(20),
    run_id VARCHAR(20),
    segment_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS walmart.products (
    product_id INTEGER PRIMARY KEY NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price FLOAT NOT NULL,
    stock INTEGER,
    lead_days INTEGER,
    ordering_cost FLOAT,
    holding_cost_per_unit FLOAT,
    eoq FLOAT,
    run_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS walmart.customers_lookup (
    customer_id SERIAL PRIMARY KEY,
    cust1_id INTEGER NULL,
    cust2_id INTEGER NULL,
    segment_id INTEGER NULL,
    run_id VARCHAR(20),

    CONSTRAINT cust1_id_unique UNIQUE (cust1_id),
    CONSTRAINT cust2_id_unique UNIQUE (cust2_id),

    CONSTRAINT fk_lookup_cust1 FOREIGN KEY (
        cust1_id
    ) REFERENCES walmart.cust1 (unique_id) ON DELETE CASCADE,

    CONSTRAINT fk_lookup_cust2 FOREIGN KEY (
        cust2_id
    ) REFERENCES walmart.cust2 (unique_id) ON DELETE CASCADE,

    CONSTRAINT custid_exist CHECK ((cust1_id IS NULL) <> (cust2_id IS NULL)) -- noqa
);


-- Combined transactions table for both customer types
CREATE TABLE IF NOT EXISTS walmart.transactions (
    transaction_id INTEGER PRIMARY KEY,
    unique_id INTEGER REFERENCES walmart.customers_lookup (customer_id),
    product_id INTEGER REFERENCES walmart.products (product_id),
    unit_price FLOAT,
    quantity INTEGER,
    date_purchased DATE,
    category VARCHAR(100),
    run_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_category ON walmart.transactions (
    category
);
CREATE INDEX IF NOT EXISTS idx_transactions_product ON walmart.transactions (
    product_id
);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON walmart.transactions (
    unique_id
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON walmart.transactions (
    date_purchased
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_lookup_cust1 ON walmart.customers_lookup (
    cust1_id
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_lookup_cust2 ON walmart.customers_lookup (
    cust2_id
);
