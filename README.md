# Project FORESIGHT – AI-Powered Demand & Inventory Intelligence

## 1. Project Overview

Project FORESIGHT is an AI-powered demand forecasting and inventory intelligence platform developed for NorthBay Living.

The system uses historical retail sales, SKU information, inventory, and promotion data to:

- Forecast weekly demand at SKU level
- Identify inventory risk
- Detect potential overstock and stockout situations
- Quantify inventory impact in Indian Rupees
- Provide prioritized business actions
- Present results through an interactive dashboard
- Provide a deployed scoring API for individual SKU predictions

---

## 2. Business Problem

Retail businesses need to maintain the right inventory level while avoiding:

- Stockouts that can cause lost sales
- Overstock that locks working capital
- Difficult manual inventory prioritization
- Limited visibility into future SKU demand

FORESIGHT addresses these problems by combining demand forecasting with inventory risk scoring.

---

## 3. Project Objectives

1. Generate weekly SKU-level demand forecasts.
2. Compare the forecasting model against a seasonal-naive baseline.
3. Identify stockout and overstock risks.
4. Recommend actions for each SKU.
5. Quantify excess inventory in rupees.
6. Provide an easy-to-use planning dashboard.
7. Provide a deployed scoring service.

---

## 4. Dataset

The project uses a synthetic retail dataset containing six CSV files:

- `bm_customers.csv`
- `bm_inventory.csv`
- `bm_promotions.csv`
- `bm_sales.csv`
- `bm_skus.csv`
- `bm_stores.csv`

The dataset contains approximately:

- 641,843 sales transactions
- 200 SKUs
- 50 stores
- 5,000 customers
- 8,735 inventory records
- 33 promotion records

Raw client/simulated data is kept outside the public repository's `archive/` directory.

---
## 5. Project Architecture

```text
Raw Retail Data
      |
      v
Data Pipeline
      |
      v
Analysis-Ready Weekly Dataset
      |
      +--------------------+
      |                    |
      v                    v
Demand Forecasting     Inventory Risk
      |                    |
      v                    v
6-Week Forecast       Risk + Action + ₹ Impact
      |                    |
      +---------+----------+
                |
                v
       Streamlit Dashboard
                |
                v
        Deployed Scoring API

```

## 6. Forecasting Model

The project uses GradientBoostingRegressor for weekly SKU-level demand forecasting.

The model uses lag, rolling, calendar, promotion, and SKU features.

### Forecasting Features

The model uses:

- Lag 1 week
- Lag 2 weeks
- Lag 4 weeks
- Lag 8 weeks
- Lag 13 weeks
- Lag 26 weeks
- Lag 52 weeks
- Rolling mean over 4 weeks
- Rolling mean over 8 weeks
- Rolling mean over 13 weeks
- Week number
- Month
- Quarter
- Year
- Promotion flag
- Promotion discount
- Promotion count
- SKU ID

Rolling features are calculated using previous demand values to avoid target leakage.

Model Configuration
Model: GradientBoostingRegressor
Number of estimators: 200
Learning rate: 0.05
Maximum depth: 3
Random state: 42

## 7. Forecast Validation

The primary evaluation method is rolling-origin time-series validation.

Three validation origins were evaluated using a six-week validation horizon.

Rolling-Origin Results
Metric	Gradient Boosting	Seasonal Naive
Average WAPE	27.48%	38.35%
Average Bias	+0.19%	+2.24%

The Gradient Boosting model achieved a relative WAPE improvement of 28.35% over the seasonal-naive baseline.

Latest Six-Week Holdout
Gradient Boosting WAPE: 32.88%
Gradient Boosting Bias: +9.32%
Seasonal Naive WAPE: 45.58%
Seasonal Naive Bias: +13.51%

The rolling-origin results are used as the primary model-validation result.

## 8. Future Forecast

The final forecasting pipeline generates a six-week forecast for 200 SKUs.

Forecast period:

2025-11-03 to 2025-12-08

The final forecast contains:

1,200 forecast records
200 SKUs
6 weeks
Weekly Forecast Totals
Week	Forecast Demand
2025-11-03	3,642.75
2025-11-10	3,666.54
2025-11-17	3,661.67
2025-11-24	3,694.91
2025-12-01	4,554.29
2025-12-08	4,532.92

Total forecasted demand across the six-week horizon is approximately:

23,753 units

Forecast output:

data/final_6_week_forecast.csv

 ## 9. Inventory Risk

The inventory risk engine combines current inventory with the six-week demand forecast to identify inventory risks.

For each SKU, the system calculates:

Six-week forecast demand
Stock coverage
Stock after forecast demand
Excess units
Shortage units
Excess inventory value
Reorder value
Forecast volatility
Priority score
Recommended decision
Risk Categories
Decision	Meaning
Reorder Now	Inventory may fall below the required level
Markdown/Clear	Inventory is significantly above expected demand
Watch/Volatile	Demand has higher uncertainty and requires monitoring
Healthy	Inventory is aligned with expected demand
Current Inventory Decisions
Decision	SKU Count
Markdown/Clear	150
Watch/Volatile	50
Reorder Now	0
Healthy	0

Estimated excess inventory value:

₹30,530,752.86 (~₹3.05 crore)

Risk output:

data/final_inventory_risk.csv

## 10. Data Pipeline

The data pipeline performs the following steps:

Loads the retail datasets.
Converts and validates date fields.
Performs data-quality checks.
Aggregates sales into weekly SKU-level demand.
Creates a complete SKU-week dataset.
Generates promotion features.
Generates calendar features.
Produces the analysis-ready dataset.

Pipeline Flow

Raw CSV Files
     |
     v
Data Loading
     |
     v
Data Quality Checks
     |
     v
Data Cleaning
     |
     v
Weekly SKU-Level Demand
     |
     v
Feature Engineering
     |
     +-------------------+
     |                   |
     v                   v
Forecasting        Inventory Risk
     |                   |
     +---------+---------+
               |
               v
      Dashboard + API

Pipeline output:

data/analysis_ready_weekly.csv

The pipeline is implemented in:

src/pipeline.py

## 11. Dashboard

The planning dashboard is built using Streamlit.

The dashboard provides:

-KPI summary
-Current inventory overview
-Six-week demand forecast
-Forecast model performance
-Category-level analysis
-Risk distribution
-Priority SKU list
-SKU-level details
-Inventory risk table
-Business insights
-Executive Summary

The dashboard displays:

Total SKUs
Current stock
Six-week forecast
Excess inventory value
Excess stock percentage
Forecast Model Performance

The dashboard displays:

-Rolling-CV model WAPE
-Seasonal-naive WAPE
-Relative improvement
-Model bias
-Latest holdout performance
-SKU-Level Intelligence

Users can select an individual SKU and inspect:

-Current stock
-Six-week forecast
-Inventory coverage
-Decision
-Excess units
-Excess value
-Forecast volatility

# Live Dashboard

https://foresight-ai-dashboard.onrender.com

## 12. Scoring Service

A FastAPI-based scoring service provides forecast and inventory-risk information for individual SKUs.

API Endpoints
GET /
GET /health
GET /score/{sku_id}

Example:

/score/1072

The service returns:

-SKU information
-Six-week forecast
-Current inventory
-Risk level
-Recommended action
-Excess units
-Shortage units
-Excess inventory value
-Reorder value

Live Scoring API
https://project-foresight-service.onrender.com/

Example SKU Endpoint
https://project-foresight-service.onrender.com/score/1072


## 13. Running the Project
Clone Repository
git clone https://github.com/samjhana-rayamajhi-cmd/project-foresight.git
cd project-foresight

Install Dependencies
pip install -r requirements.txt

Run Data Pipeline
py src/pipeline.py

Run Forecasting
py src/forecast.py

Run Inventory Risk Analysis
py src/risk.py

Run Dashboard
py -m streamlit run app/app.py

The dashboard will be available locally at:
http://localhost:8501

## 14. Repository Structure
project-foresight/
│
├── app/
│   └── app.py
│
├── data/
│   ├── analysis_ready_weekly.csv
│   ├── final_6_week_forecast.csv
│   └── final_inventory_risk.csv
│
├── service/
│   ├── service.py
│   └── requirements.txt
│
├── src/
│   ├── pipeline.py
│   ├── forecast.py
│   └── risk.py
│
├── requirements.txt
├── README.md
└── .gitignore


## 15. Technology Stack
Programming Language
      Python
Data Processing
      pandas
      NumPy
Machine Learning
      scikit-learn
      Gradient Boosting Regression
Dashboard
      Streamlit
      Plotly
API
      FastAPI
      Uvicorn
Deployment
      Render
Version Control
      Git
      GitHub


## 16. Data Quality

The project performs data-quality checks on the supplied retail datasets.

The checks include:

-Missing values
-Duplicate records
-Negative quantities
-Negative prices
-Invalid inventory values
-Date validation
-SKU consistency
-Store consistency
-Customer consistency

The sales dataset contains missing customer IDs.

These records were retained because customer identity is not required for SKU-level demand forecasting.

The final analysis-ready dataset contains:

50,600 SKU-week records
200 SKUs
253 weeks

The weekly dataset uses a complete SKU-week grid to support consistent forecasting across all SKUs.



## 17. Assumptions

The project uses the following assumptions:

1.Historical SKU-level demand can provide useful information for future demand forecasting.
2.Weekly aggregation is appropriate for inventory planning.
3.Seasonal-naive forecasting provides a useful baseline for comparison.
4.The latest available inventory snapshot represents the current inventory position.
5.Inventory risk can be evaluated using forecast demand, current stock, reorder point, safety stock and forecast volatility.
6.Excess inventory value is calculated using the available product cost information.
7.The six-week forecast horizon is used for inventory planning.
8.The supplied inventory data represents a snapshot rather than a complete historical inventory series.



## 18. Business Insights
Strong Seasonal Demand

The weekly demand data shows a clear seasonal pattern.

Average weekly demand varies substantially across the year, indicating that seasonality is an important factor for demand planning.

Category Demand
The analyzed dataset contains demand across:

-Electronics
-Snacks
-Household
-Dairy
-Grocery
-Personal Care
-Beverages

Electronics currently has the highest excess inventory value in the selected portfolio.

Excess Inventory Exposure
The current inventory analysis identifies approximately:

₹30.53 million of excess inventory value.

This represents a significant working-capital exposure that can be prioritized through inventory clearance and monitoring actions.

Priority SKU

SKU 1072 is currently ranked as the highest-priority SKU in the selected portfolio.

Its current decision is:

Watch/Volatile


## 19. Project Scope
Included
      Weekly SKU-level demand forecasting
      Seasonal-naive baseline
      Rolling-origin validation
      Inventory risk scoring
      Excess inventory identification
      Recommended inventory actions
      Rupee impact estimation
      Interactive dashboard
      Deployed scoring API

Not Included
      Live ERP integration
      Real-time inventory streaming
      Supplier selection
      Price optimization
      Automated purchase-order placement
      Full inventory optimization
      Automated procurement decisions

The project is intended as a demand forecasting and inventory decision-support system.


## 20. Limitations

The current solution has several limitations.

Inventory History
The available inventory data is a snapshot rather than a complete historical inventory time series.
Therefore, inventory risk is calculated using the latest available inventory position.


Customer Information
Some sales records do not contain customer IDs.
These records are retained because customer-level information is not required for SKU-level demand forecasting.


Forecast Uncertainty
Forecasts are estimates and actual future demand may differ from predicted demand.
The system therefore combines forecast information with inventory and volatility indicators.

External Factors

The current model does not explicitly include all external demand drivers, such as:

-Competitor activity
-Weather
-Macroeconomic conditions
-Supplier disruptions
-Unexpected market events



## 21. Reproducibility

The project can be reproduced by running the main pipeline components in sequence.

Step 1 — Generate Analysis-Ready Data
py src/pipeline.py

Step 2 — Generate Six-Week Forecast
py src/forecast.py

Step 3 — Generate Inventory Risk
py src/risk.py

Step 4 — Launch Dashboard
py -m streamlit run app/app.py

The main generated outputs are:

data/analysis_ready_weekly.csv
data/final_6_week_forecast.csv
data/final_inventory_risk.csv



## 22. Project Results
Forecasting Result

The Gradient Boosting model achieved:

27.48% average rolling-origin WAPE

compared with:

38.35% seasonal-naive WAPE

Relative improvement:

28.35%

Average rolling-origin model bias:

+0.19%

Inventory Result

The system identified:

₹30,530,752.86

of estimated excess inventory value.

Current inventory decisions:

150 SKUs — Markdown/Clear
50 SKUs — Watch/Volatile
0 SKUs — Reorder Now
0 SKUs — Healthy
Forecast Output

The final forecast covers:

200 SKUs
6 weeks
1,200 SKU-week predictions

Total six-week forecast demand:

23,753 units


## 23. Live Project Links
GitHub Repository

https://github.com/samjhana-rayamajhi-cmd/project-foresight

Live Dashboard

https://foresight-ai-dashboard.onrender.com

Live Scoring API

https://project-foresight-service.onrender.com/

Example SKU Endpoint

https://project-foresight-service.onrender.com/score/1072



## 24. Conclusion

Project FORESIGHT provides an end-to-end demand forecasting and inventory intelligence solution for retail planning.

The system combines:

      Data preparation
      Exploratory analysis
      Machine learning forecasting
      Forecast validation
      Inventory risk scoring
      Business prioritization
      Interactive visualization
      API deployment

The Gradient Boosting model achieved an average rolling-origin WAPE of 27.48%, compared with 38.35% for the seasonal-naive baseline.

This represents a 28.35% relative improvement in WAPE.

The inventory analysis identified approximately ₹30.53 million of estimated excess inventory value across the current portfolio.

The final solution provides both a business-facing dashboard and a deployed scoring service to support demand and inventory planning.

## Project Information

Project: FORESIGHT – AI-Powered Demand & Inventory Intelligence Platform

Client: NorthBay Living

Role: Data Scientist