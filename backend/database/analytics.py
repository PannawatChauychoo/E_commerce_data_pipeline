import duckdb

def analyze_sales():
    # Direct integration with Pandas
    duck = duckdb.connect('walmart_analytics.db')
    
    # Can read directly from your Postgres tables
    duck.sql("""
        SELECT date_trunc('day', date_purchase) as day,
               sum(quantity * unit_price) as revenue
        FROM postgres_scan('postgresql://user:pass@host/db', 'transactions')
        GROUP BY 1
        ORDER BY 1
    """)