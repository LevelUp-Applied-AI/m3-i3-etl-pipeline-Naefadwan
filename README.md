[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Nvxy3054)
# ETL Pipeline — Amman Digital Market

## Overview

Amman Digital Market is a fictional e-commerce platform. This ETL pipeline extracts raw data from a PostgreSQL database, transforms it into an analytical summary of customer behavior, validates the data for quality and consistency, and loads the results back into the database and a CSV file for further analysis.

The pipeline focuses on:
- Cleaning data by filtering cancelled orders and erroneous quantities.
- Aggregating metrics like total orders, total revenue, and average order value.
- Identifying the `top_category` for each customer based on their spending.

## Setup

1. Start PostgreSQL container:
   ```bash
   docker run -d --name postgres-m3-int \
     -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=amman_market \
     -p 5432:5432 -v pgdata_m3_int:/var/lib/postgresql/data \
     postgres:15-alpine
   ```
2. Load schema and data:
   ```bash
   docker exec -i postgres-m3-int psql -U postgres -d amman_market -f - < schema.sql
   docker exec -i postgres-m3-int psql -U postgres -d amman_market -f - < seed_data.sql
   ```
3. Install dependencies: `pip install -r requirements.txt`

## How to Run

```bash
python etl_pipeline.py
```

## Output

The pipeline generates a `customer_analytics.csv` file in the `output/` directory and a `customer_analytics` table in the database. These contains:
- `customer_id`: Unique identifier for the customer.
- `customer_name`: Full name of the customer.
- `city`: The city where the customer is located.
- `total_orders`: Count of distinct completed orders.
- `total_revenue`: Sum of all line totals for completed orders.
- `avg_order_value`: Average spending per order.
- `top_category`: The product category where the customer spent the most money.

## Quality Checks

The `validate()` function performs the following checks to ensure data integrity:
- **`no_null_id`**: Ensures every record has a `customer_id`. Null IDs would break joins and reporting.
- **`no_null_name`**: Ensures every record has a `customer_name` for presentation layers.
- **`revenue_positive`**: Verifies that `total_revenue` is always greater than zero. Revenue cannot be negative or zero for active customers in this summary.
- **`unique_ids`**: Confirms that each `customer_id` appears only once in the summary.
- **`orders_positive`**: Ensures `total_orders` is greater than zero.

If any of these critical checks fail, the pipeline raises a `ValueError` and halts execution to prevent loading "dirty" data.

---

## License

This repository is provided for educational use only. See [LICENSE](LICENSE) for terms.

You may clone and modify this repository for personal learning and practice, and reference code you wrote here in your professional portfolio. Redistribution outside this course is not permitted.
