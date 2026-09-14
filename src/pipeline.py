import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT FORESIGHT - DATA PIPELINE
# ============================================================

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "archive"
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# 1. LOAD RAW DATA
# ============================================================

def load_data():

    sales = pd.read_csv(RAW_DIR / "bm_sales.csv")
    skus = pd.read_csv(RAW_DIR / "bm_skus.csv")
    inventory = pd.read_csv(RAW_DIR / "bm_inventory.csv")
    promotions = pd.read_csv(RAW_DIR / "bm_promotions.csv")

    return sales, skus, inventory, promotions


# ============================================================
# 2. CLEAN DATA
# ============================================================

def clean_data(sales, skus, inventory, promotions):

    # Convert dates
    sales["date"] = pd.to_datetime(
        sales["date"],
        errors="coerce"
    )

    promotions["start_date"] = pd.to_datetime(
        promotions["start_date"],
        errors="coerce"
    )

    promotions["end_date"] = pd.to_datetime(
        promotions["end_date"],
        errors="coerce"
    )

    inventory["last_restock_date"] = pd.to_datetime(
        inventory["last_restock_date"],
        errors="coerce"
    )

    inventory["snapshot_date"] = pd.to_datetime(
        inventory["snapshot_date"],
        errors="coerce"
    )

    # Remove exact duplicate records
    sales = sales.drop_duplicates().copy()
    skus = skus.drop_duplicates().copy()
    inventory = inventory.drop_duplicates().copy()
    promotions = promotions.drop_duplicates().copy()

    # Remove rows with invalid essential identifiers
    sales = sales.dropna(
        subset=["date", "sku_id", "quantity"]
    ).copy()

    skus = skus.dropna(
        subset=["sku_id"]
    ).copy()

    inventory = inventory.dropna(
        subset=["sku_id", "stock_on_hand"]
    ).copy()

    promotions = promotions.dropna(
        subset=["start_date", "end_date"]
    ).copy()

    # Ensure numeric columns are numeric
    numeric_sales = [
        "quantity",
        "unit_price",
        "total_value",
        "discount_pct"
    ]

    for col in numeric_sales:
        if col in sales.columns:
            sales[col] = pd.to_numeric(
                sales[col],
                errors="coerce"
            )

    inventory_numeric = [
        "stock_on_hand",
        "reorder_point",
        "safety_stock"
    ]

    for col in inventory_numeric:
        if col in inventory.columns:
            inventory[col] = pd.to_numeric(
                inventory[col],
                errors="coerce"
            )

    return sales, skus, inventory, promotions


# ============================================================
# 3. CREATE WEEKLY SKU-LEVEL DATASET
# ============================================================

def create_weekly_dataset(sales, skus, promotions):

    # Merge sales with SKU master
    sales_sku = sales.merge(
        skus,
        on="sku_id",
        how="left"
    )

    # Create weekly period
    sales_sku["week"] = (
        sales_sku["date"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    # Aggregate sales to weekly SKU level
    weekly_sales = (
        sales_sku
        .groupby(
            ["week", "sku_id"],
            as_index=False
        )
        .agg(
            demand=("quantity", "sum"),
            sales_value=("total_value", "sum"),
            avg_price=("unit_price_x", "mean"),
            avg_discount=("discount_pct", "mean")
        )
    )

    # Create complete week-SKU grid
    all_weeks = pd.date_range(
        start=weekly_sales["week"].min(),
        end=weekly_sales["week"].max(),
        freq="7D"
    )

    all_skus = skus["sku_id"].unique()

    complete_grid = pd.MultiIndex.from_product(
        [all_weeks, all_skus],
        names=["week", "sku_id"]
    ).to_frame(index=False)

    weekly_sales_complete = complete_grid.merge(
        weekly_sales,
        on=["week", "sku_id"],
        how="left"
    )

    # Fill missing weekly observations
    zero_columns = [
        "demand",
        "sales_value",
        "avg_price",
        "avg_discount"
    ]

    weekly_sales_complete[zero_columns] = (
        weekly_sales_complete[zero_columns]
        .fillna(0)
    )

    # Add SKU information
    weekly_sales_complete = weekly_sales_complete.merge(
        skus[
            [
                "sku_id",
                "sku_name",
                "category",
                "subcategory",
                "brand",
                "cost_price"
            ]
        ],
        on="sku_id",
        how="left"
    )

        # ========================================================
    # Promotion features
    # ========================================================

    promotions = promotions.copy()

    promo_rows = []

    # Create one record for each promotion-week
    # This matches the forecasting notebook methodology.
    for _, row in promotions.iterrows():

        weeks = pd.date_range(
            start=row["start_date"].to_period("W-SUN").start_time,
            end=row["end_date"].to_period("W-SUN").start_time,
            freq="7D"
        )

        for week in weeks:

            promo_rows.append(
                {
                    "week": week,
                    "promo_type": row["promo_type"],
                    "discount_pct": row["discount_pct"]
                }
            )

    if promo_rows:

        promo_weekly = pd.DataFrame(promo_rows)

        # Aggregate promotions to one row per week
        promo_weekly = (
            promo_weekly
            .groupby("week", as_index=False)
            .agg(
                promo_flag=("promo_type", lambda x: 1),
                promo_discount=("discount_pct", "max"),
                promo_count=("promo_type", "count")
            )
        )

    else:

        promo_weekly = pd.DataFrame(
            columns=[
                "week",
                "promo_flag",
                "promo_discount",
                "promo_count"
            ]
        )

    # Merge promotion information
    weekly_sales_complete = weekly_sales_complete.merge(
        promo_weekly,
        on="week",
        how="left"
    )

    weekly_sales_complete[
        [
            "promo_flag",
            "promo_discount",
            "promo_count"
        ]
    ] = weekly_sales_complete[
        [
            "promo_flag",
            "promo_discount",
            "promo_count"
        ]
    ].fillna(0)

    # Save analysis-ready dataset
    output_path = DATA_DIR / "analysis_ready_weekly.csv"

    weekly_sales_complete.to_csv(
        output_path,
        index=False
    )

    return weekly_sales_complete


# ============================================================
# 4. RUN PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("PROJECT FORESIGHT - DATA PIPELINE")
    print("=" * 60)

    print("\nLoading raw data...")

    sales, skus, inventory, promotions = load_data()

    print(f"Sales:       {sales.shape}")
    print(f"SKUs:        {skus.shape}")
    print(f"Inventory:   {inventory.shape}")
    print(f"Promotions:  {promotions.shape}")

    print("\nCleaning data...")

    sales, skus, inventory, promotions = clean_data(
        sales,
        skus,
        inventory,
        promotions
    )

    print("Cleaning completed.")

    print("\nCreating weekly SKU-level dataset...")

    weekly_data = create_weekly_dataset(
        sales,
        skus,
        promotions
    )

    print(
        f"Analysis-ready dataset: {weekly_data.shape}"
    )

    print(
        f"\nSaved to:\n"
        f"{DATA_DIR / 'analysis_ready_weekly.csv'}"
    )

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()