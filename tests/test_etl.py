"""Tests for the ETL pipeline.

Write at least 3 tests:
1. test_transform_filters_cancelled — cancelled orders excluded after transform
2. test_transform_filters_suspicious_quantity — quantities > 100 excluded
3. test_validate_catches_nulls — validate() raises ValueError on null customer_id
"""
from etl_pipeline import transform, validate
import pandas as pd
import pytest


@pytest.fixture
def sample_data():
    customers = pd.DataFrame({
        "customer_id": [1, 2],
        "customer_name": ["Alice", "Bob"],
        "city": ["Amman", "Zarqa"]
    })
    products = pd.DataFrame({
        "product_id": [101, 102],
        "product_name": ["Laptop", "Mouse"],
        "category": ["Electronics", "Accessories"],
        "unit_price": [1000.0, 50.0]
    })
    orders = pd.DataFrame({
        "order_id": [1001, 1002, 1003],
        "customer_id": [1, 1, 2],
        "status": ["completed", "cancelled", "completed"]
    })
    order_items = pd.DataFrame({
        "item_id": [1, 2, 3],
        "order_id": [1001, 1002, 1003],
        "product_id": [101, 102, 101],
        "quantity": [1, 1, 1]
    })
    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items
    }


def test_transform_filters_cancelled(sample_data):
    """Create test DataFrames with a cancelled order. Confirm it's excluded."""
    result = transform(sample_data)
    # Order 1002 is cancelled, so Alice should only have 1 order (1001)
    alice_row = result[result["customer_id"] == 1].iloc[0]
    assert alice_row["total_orders"] == 1
    assert alice_row["total_revenue"] == 1000.0


def test_transform_filters_suspicious_quantity(sample_data):
    """Create test DataFrames with quantity > 100. Confirm it's excluded."""
    # Add a suspicious quantity item
    sample_data["order_items"].loc[0, "quantity"] = 150
    result = transform(sample_data)
    # Order 1001 (quantity 150) should be excluded.
    # Alice now has 0 completed orders (1001 excluded, 1002 cancelled)
    assert 1 not in result["customer_id"].values


def test_validate_catches_nulls():
    """Create a DataFrame with null customer_id. Confirm validate() raises ValueError."""
    df = pd.DataFrame({
        "customer_id": [1, None],
        "customer_name": ["Alice", "Bob"],
        "total_revenue": [100, 200],
        "total_orders": [1, 2]
    })
    with pytest.raises(ValueError, match="no_null_id"):
        validate(df)
