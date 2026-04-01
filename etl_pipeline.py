"""ETL Pipeline — Amman Digital Market Customer Analytics

Extracts data from PostgreSQL, transforms it into customer-level summaries,
validates data quality, and loads results to a database table and CSV file.
"""
from sqlalchemy import create_engine
import pandas as pd
import os


def extract(engine):
    """Extract all source tables from PostgreSQL into DataFrames.

    Args:
        engine: SQLAlchemy engine connected to the amman_market database

    Returns:
        dict: {"customers": df, "products": df, "orders": df, "order_items": df}
    """
    tables = ["customers", "products", "orders", "order_items"]
    data = {}
    for table in tables:
        data[table] = pd.read_sql_table(table, engine)
    return data


def transform(data_dict):
    """Transform raw data into customer-level analytics summary.

    Steps:
    1. Join orders with order_items and products
    2. Compute line_total (quantity * unit_price)
    3. Filter out cancelled orders (status = 'cancelled')
    4. Filter out suspicious quantities (quantity > 100)
    5. Aggregate to customer level: total_orders, total_revenue,
       avg_order_value, top_category

    Args:
        data_dict: dict of DataFrames from extract()

    Returns:
        DataFrame: customer-level summary with columns:
            customer_id, customer_name, city, total_orders,
            total_revenue, avg_order_value, top_category
    """
    customers = data_dict["customers"]
    products = data_dict["products"]
    orders = data_dict["orders"]
    order_items = data_dict["order_items"]

    # 1. Join tables
    df = (
        orders.merge(order_items, on="order_id")
        .merge(products, on="product_id")
        .merge(customers, on="customer_id")
    )

    # 2. Compute line_total
    df["line_total"] = df["quantity"] * df["unit_price"]

    # 3. Filter out cancelled orders
    df = df[df["status"] != "cancelled"]

    # 4. Filter out suspicious quantities
    df = df[df["quantity"] <= 100]

    # 5. Aggregate to customer level
    # First, calculate top_category per customer
    category_revenue = (
        df.groupby(["customer_id", "category"])["line_total"]
        .sum()
        .reset_index()
    )
    top_category = (
        category_revenue.sort_values("line_total", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})[["customer_id", "top_category"]]
    )

    # Main aggregation
    customer_summary = (
        df.groupby(["customer_id", "customer_name", "city"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("line_total", "sum"),
        )
        .reset_index()
    )

    # Calculate avg_order_value
    customer_summary["avg_order_value"] = (
        customer_summary["total_revenue"] / customer_summary["total_orders"]
    )

    # Merge with top_category
    customer_summary = customer_summary.merge(top_category, on="customer_id", how="left")

    return customer_summary


def validate(df):
    """Run data quality checks on the transformed DataFrame.

    Checks:
    - No nulls in customer_id or customer_name
    - total_revenue > 0 for all customers
    - No duplicate customer_ids
    - total_orders > 0 for all customers

    Args:
        df: transformed customer summary DataFrame

    Returns:
        dict: {check_name: bool} for each check

    Raises:
        ValueError: if any critical check fails
    """
    checks = {
        "no_null_id": not df["customer_id"].isnull().any(),
        "no_null_name": not df["customer_name"].isnull().any(),
        "revenue_positive": (df["total_revenue"] > 0).all(),
        "unique_ids": df["customer_id"].is_unique,
        "orders_positive": (df["total_orders"] > 0).all(),
    }

    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"Data Quality Check: {check} - {status}")
        if not result:
            raise ValueError(f"Critical check failed: {check}")

    return checks


def load(df, engine, csv_path):
    """Load customer summary to PostgreSQL table and CSV file.

    Args:
        df: validated customer summary DataFrame
        engine: SQLAlchemy engine
        csv_path: path for CSV output
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # 1. Save to PostgreSQL
    df.to_sql("customer_analytics", engine, if_exists="replace", index=False)

    # 2. Save to CSV
    df.to_csv(csv_path, index=False)

    print(f"Successfully loaded {len(df)} rows to {csv_path} and 'customer_analytics' table.")


def main():
    """Orchestrate the ETL pipeline: extract -> transform -> validate -> load."""
    print("Starting ETL pipeline...")

    # 1. Create engine from DATABASE_URL env var (or default)
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/amman_market")
    engine = create_engine(db_url)

    # 2. Extract
    print("Extracting data...")
    data_dict = extract(engine)
    print(f"Extracted {len(data_dict['customers'])} customers, {len(data_dict['orders'])} orders.")

    # 3. Transform
    print("Transforming data...")
    summary_df = transform(data_dict)
    print(f"Transformed to {len(summary_df)} customer-level summary rows.")

    # 4. Validate
    print("Validating data...")
    validate(summary_df)

    # 5. Load to customer_summary table and output/customer_analytics.csv
    print("Loading data...")
    csv_path = os.path.join("output", "customer_analytics.csv")
    load(summary_df, engine, csv_path)

    print("ETL pipeline completed successfully!")


if __name__ == "__main__":
    main()
