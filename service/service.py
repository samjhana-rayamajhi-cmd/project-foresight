from fastapi import FastAPI, HTTPException
import pandas as pd
from pathlib import Path

app = FastAPI(
    title="Project FORESIGHT Scoring Service",
    description="Demand forecast and inventory risk scoring API",
    version="1.0"
)

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FORECAST_FILE = DATA_DIR / "final_6_week_forecast.csv"
RISK_FILE = DATA_DIR / "final_inventory_risk.csv"


# Load project outputs
try:
    forecast_df = pd.read_csv(FORECAST_FILE)
    risk_df = pd.read_csv(RISK_FILE)
except Exception as e:
    raise RuntimeError(f"Could not load project data: {e}")


@app.get("/")
def home():
    return {
        "service": "Project FORESIGHT Scoring Service",
        "status": "running",
        "description": "Returns 6-week demand forecast and inventory risk"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "forecast_rows": len(forecast_df),
        "risk_rows": len(risk_df)
    }


@app.get("/score/{sku_id}")
def score_sku(sku_id: int):

    # Find forecast for requested SKU
    sku_forecast = forecast_df[
        forecast_df["sku_id"] == sku_id
    ].copy()

    # Find inventory risk for requested SKU
    sku_risk = risk_df[
        risk_df["sku_id"] == sku_id
    ].copy()

    # Handle invalid SKU
    if sku_forecast.empty or sku_risk.empty:
        raise HTTPException(
            status_code=404,
            detail=f"SKU {sku_id} was not found"
        )

    # Build forecast response
    forecast_records = []

    for _, row in sku_forecast.iterrows():
        forecast_records.append({
            "week": str(row["week"]),
            "forecast_demand": round(
                float(row["forecast_demand"]), 2
            )
        })

    # Inventory information
    risk = sku_risk.iloc[0]

    decision = str(risk["decision"])

    # Convert decision into a simple risk level
    if decision == "Reorder Now":
        risk_level = "Stockout Risk"
    elif decision == "Markdown/Clear":
        risk_level = "Overstock Risk"
    elif decision == "Watch/Volatile":
        risk_level = "Watch"
    else:
        risk_level = "Healthy"

    return {
        "sku_id": sku_id,
        "sku_name": str(risk["sku_name"]),
        "category": str(risk["category"]),

        "forecast": forecast_records,

        "inventory_risk": {
            "risk_level": risk_level,
            "decision": decision,
            "recommended_action": decision,
            "current_stock": int(risk["stock_on_hand"]),
            "six_week_forecast": round(
                float(risk["forecast_6_week_demand"]), 2
            ),
            "excess_units": round(
                float(risk["excess_units"]), 2
            ),
            "shortage_units": round(
                float(risk["shortage_units"]), 2
            ),
            "excess_value": round(
                float(risk["excess_value"]), 2
            ),
            "reorder_value": round(
                float(risk["reorder_value"]), 2
            )
        }
    }