import pandas as pd
import numpy as np

from pathlib import Path


# ============================================================
# PROJECT FORESIGHT - INVENTORY RISK
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "archive"

DATA_DIR = BASE_DIR / "data"


# ============================================================
# INVENTORY RISK FUNCTION
# ============================================================

def run_inventory_risk():

    inventory_path = (
        RAW_DIR /
        "bm_inventory.csv"
    )

    skus_path = (
        RAW_DIR /
        "bm_skus.csv"
    )

    forecast_path = (
        DATA_DIR /
        "final_6_week_forecast.csv"
    )

    output_path = (
        DATA_DIR /
        "final_inventory_risk.csv"
    )

    print("\n" + "=" * 60)
    print("PROJECT FORESIGHT - INVENTORY RISK")
    print("=" * 60)

    # ========================================================
    # LOAD DATA
    # ========================================================

    print("\nLoading inventory data...")

    inventory = pd.read_csv(
        inventory_path
    )

    skus = pd.read_csv(
        skus_path
    )

    forecast = pd.read_csv(
        forecast_path
    )

    print(
        "Inventory:",
        inventory.shape
    )

    print(
        "SKUs:",
        skus.shape
    )

    print(
        "Forecast:",
        forecast.shape
    )

    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    inventory_columns = [
        "stock_on_hand",
        "reorder_point",
        "safety_stock"
    ]

    for col in inventory_columns:

        inventory[col] = pd.to_numeric(
            inventory[col],
            errors="coerce"
        )

    skus["cost_price"] = pd.to_numeric(
        skus["cost_price"],
        errors="coerce"
    )

    forecast["forecast_demand"] = pd.to_numeric(
        forecast["forecast_demand"],
        errors="coerce"
    )

    # ========================================================
    # AGGREGATE INVENTORY BY SKU
    # ========================================================

    print("\nAggregating inventory by SKU...")

    inventory_agg = (
        inventory
        .groupby(
            "sku_id",
            as_index=False
        )
        .agg(
            stock_on_hand=(
                "stock_on_hand",
                "sum"
            ),

            reorder_point=(
                "reorder_point",
                "sum"
            ),

            safety_stock=(
                "safety_stock",
                "sum"
            )
        )
    )

    print(
        "Aggregated inventory:",
        inventory_agg.shape
    )

    # ========================================================
    # AGGREGATE FORECAST
    # ========================================================

    forecast_summary = (
        forecast
        .groupby(
            "sku_id",
            as_index=False
        )
        .agg(

            forecast_6_week_demand=(
                "forecast_demand",
                "sum"
            ),

            avg_weekly_forecast=(
                "forecast_demand",
                "mean"
            ),

            min_weekly_forecast=(
                "forecast_demand",
                "min"
            ),

            max_weekly_forecast=(
                "forecast_demand",
                "max"
            ),

            forecast_std=(
                "forecast_demand",
                "std"
            )
        )
    )

    # Population-style CV used for the final risk analysis
    forecast_cv_group = (
        forecast
        .groupby("sku_id")["forecast_demand"]
        .agg(
            ["mean", "std"]
        )
    )

    # Use standard deviation divided by mean
    forecast_summary["forecast_cv"] = (
        forecast_summary["forecast_std"]
        /
        forecast_summary["avg_weekly_forecast"]
    )

    forecast_summary["forecast_cv"] = (
        forecast_summary["forecast_cv"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # ========================================================
    # MERGE INVENTORY + FORECAST
    # ========================================================

    inventory_risk = inventory_agg.merge(
        forecast_summary,
        on="sku_id",
        how="inner"
    )

    # ========================================================
    # ADD SKU INFORMATION
    # ========================================================

    inventory_risk = inventory_risk.merge(
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
    # COVERAGE AND STOCK POSITION
    # ========================================================

    inventory_risk["coverage_weeks"] = (
        inventory_risk["stock_on_hand"]
        /
        inventory_risk["avg_weekly_forecast"]
    )

    inventory_risk["stock_after_6_week_demand"] = (
        inventory_risk["stock_on_hand"]
        -
        inventory_risk["forecast_6_week_demand"]
    )

    inventory_risk["stock_vs_reorder_point"] = (
        inventory_risk["stock_on_hand"]
        -
        inventory_risk["reorder_point"]
    )

    inventory_risk["stock_vs_safety_stock"] = (
        inventory_risk["stock_on_hand"]
        -
        inventory_risk["safety_stock"]
    )

    # ========================================================
    # TARGET STOCK
    # ========================================================

    inventory_risk["target_stock"] = (
        inventory_risk["forecast_6_week_demand"]
        +
        inventory_risk["safety_stock"]
    )

    # ========================================================
    # EXCESS / SHORTAGE
    # ========================================================

    inventory_risk["excess_units"] = (
        inventory_risk["stock_on_hand"]
        -
        inventory_risk["target_stock"]
    ).clip(lower=0)

    inventory_risk["shortage_units"] = (
        inventory_risk["target_stock"]
        -
        inventory_risk["stock_on_hand"]
    ).clip(lower=0)

    # ========================================================
    # RUPEE IMPACT
    # ========================================================

    inventory_risk["excess_value"] = (
        inventory_risk["excess_units"]
        *
        inventory_risk["cost_price"]
    )

    inventory_risk["reorder_value"] = (
        inventory_risk["shortage_units"]
        *
        inventory_risk["cost_price"]
    )

    # ========================================================
    # EXCESS PERCENTAGE
    # ========================================================

    inventory_risk["excess_percentage"] = (
        inventory_risk["excess_units"]
        /
        inventory_risk["stock_on_hand"]
    ) * 100

    # ========================================================
    # SIGNIFICANT EXCESS
    # ========================================================

    inventory_risk["significant_excess"] = (
        inventory_risk["excess_units"]
        >
        inventory_risk["safety_stock"]
    )

    # ========================================================
    # VOLATILITY THRESHOLD
    # ========================================================

    volatility_threshold = (
        inventory_risk["forecast_cv"]
        .quantile(0.75)
    )

    print(
        "\nVolatility threshold:",
        volatility_threshold
    )

    # ========================================================
    # DECISION CLASSIFICATION
    # ========================================================

    def classify_inventory(row):

        if (
            row["stock_on_hand"]
            <
            row["target_stock"]
        ):
            return "Reorder Now"

        elif (
            row["significant_excess"]
            and
            row["forecast_cv"]
            <=
            volatility_threshold
        ):
            return "Markdown/Clear"

        elif (
            row["significant_excess"]
            and
            row["forecast_cv"]
            >
            volatility_threshold
        ):
            return "Watch/Volatile"

        else:
            return "Healthy"

    inventory_risk["decision"] = (
        inventory_risk
        .apply(
            classify_inventory,
            axis=1
        )
    )

    # ========================================================
    # PRIORITY SCORE
    # ========================================================

    excess_value_score = (
        inventory_risk["excess_value"]
        /
        inventory_risk["excess_value"].max()
    )

    volatility_score = (
        inventory_risk["forecast_cv"]
        /
        inventory_risk["forecast_cv"].max()
    )

    excess_percentage_score = (
        inventory_risk["excess_percentage"]
        /
        inventory_risk["excess_percentage"].max()
    )

    inventory_risk["priority_score"] = (
        0.5 * excess_value_score
        +
        0.3 * excess_percentage_score
        +
        0.2 * volatility_score
    )

    # ========================================================
    # PRIORITY RANK
    # ========================================================

    inventory_risk["priority_rank"] = (
        inventory_risk["priority_score"]
        .rank(
            ascending=False,
            method="first"
        )
        .astype(int)
    )

    # ========================================================
    # FINAL COLUMNS
    # ========================================================

    final_inventory_columns = [

        "sku_id",
        "sku_name",
        "category",
        "subcategory",
        "brand",
        "cost_price",

        "stock_on_hand",
        "reorder_point",
        "safety_stock",

        "forecast_6_week_demand",
        "avg_weekly_forecast",
        "min_weekly_forecast",
        "max_weekly_forecast",

        "coverage_weeks",

        "stock_after_6_week_demand",

        "stock_vs_reorder_point",

        "stock_vs_safety_stock",

        "target_stock",

        "excess_units",
        "shortage_units",

        "excess_value",
        "reorder_value",

        "forecast_std",
        "forecast_cv",

        "excess_percentage",

        "decision",

        "priority_score",
        "priority_rank"
    ]

    final_inventory_risk = (
        inventory_risk[
            final_inventory_columns
        ]
        .copy()
    )

    # ========================================================
    # SAVE
    # ========================================================

    final_inventory_risk.to_csv(
        output_path,
        index=False
    )

    print(
        "\nFinal inventory risk shape:",
        final_inventory_risk.shape
    )

    print(
        "Missing values:",
        final_inventory_risk
        .isnull()
        .sum()
        .sum()
    )

    print(
        "\nDecision counts:"
    )

    print(
        final_inventory_risk[
            "decision"
        ].value_counts()
    )

    print(
        "\nTotal excess value:",
        f"₹{final_inventory_risk['excess_value'].sum():,.2f}"
    )

    print(
        f"\nSaved to:\n{output_path}"
    )

    print(
        "\nInventory risk completed!"
    )

    return final_inventory_risk


if __name__ == "__main__":
    run_inventory_risk()