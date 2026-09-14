import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# PROJECT FORESIGHT - INVENTORY INTELLIGENCE DASHBOARD
# ============================================================


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FORESIGHT | Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f5f7fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .dashboard-subtitle {
        font-size: 18px;
        color: #666666;
        margin-top: 0px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


INVENTORY_FILE = DATA_DIR / "final_inventory_risk.csv"
FORECAST_FILE = DATA_DIR / "final_6_week_forecast.csv"
WEEKLY_FILE = DATA_DIR / "analysis_ready_weekly.csv"


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    inventory = pd.read_csv(
        INVENTORY_FILE
    )

    forecast = pd.read_csv(
        FORECAST_FILE
    )

    weekly = pd.read_csv(
        WEEKLY_FILE
    )

    inventory["sku_id"] = inventory["sku_id"].astype(int)

    forecast["sku_id"] = forecast["sku_id"].astype(int)

    weekly["sku_id"] = weekly["sku_id"].astype(int)

    forecast["week"] = pd.to_datetime(
        forecast["week"]
    )

    weekly["week"] = pd.to_datetime(
        weekly["week"]
    )

    return inventory, forecast, weekly


# ============================================================
# LOAD
# ============================================================

try:

    inventory, forecast, weekly = load_data()

except Exception as e:

    st.error(
        "Unable to load dashboard data."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">📦 PROJECT FORESIGHT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'AI-Powered Demand & Inventory Intelligence Platform'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "**NorthBay Living** | "
    "Demand Forecasting • Inventory Risk • Decision Intelligence"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🎛️ Dashboard Controls"
)

st.sidebar.markdown(
    "Use the filters below to explore inventory risk."
)


categories = [
    "All"
] + sorted(
    inventory[
        "category"
    ]
    .dropna()
    .unique()
    .tolist()
)


selected_category = st.sidebar.selectbox(
    "📂 Category",
    categories
)


decisions = [
    "All"
] + sorted(
    inventory[
        "decision"
    ]
    .dropna()
    .unique()
    .tolist()
)


selected_decision = st.sidebar.selectbox(
    "⚠️ Risk Decision",
    decisions
)


st.sidebar.divider()


st.sidebar.info(
    """
**Forecast Horizon**

Next 6 weeks

**Primary Metric**

WAPE

**Risk Framework**

Reorder • Markdown • Watch • Healthy
"""
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_inventory = inventory.copy()


if selected_category != "All":

    filtered_inventory = filtered_inventory[
        filtered_inventory["category"]
        == selected_category
    ]


if selected_decision != "All":

    filtered_inventory = filtered_inventory[
        filtered_inventory["decision"]
        == selected_decision
    ]


# ============================================================
# EXECUTIVE KPI CALCULATIONS
# ============================================================

total_skus = len(
    filtered_inventory
)


total_stock = filtered_inventory[
    "stock_on_hand"
].sum()


total_forecast = filtered_inventory[
    "forecast_6_week_demand"
].sum()


total_excess_value = filtered_inventory[
    "excess_value"
].sum()


total_excess_units = filtered_inventory[
    "excess_units"
].sum()


excess_percentage = (

    total_excess_units
    / total_stock
    * 100

    if total_stock > 0
    else 0
)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📊 Executive Summary'
    '</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.metric(
        "Total SKUs",
        f"{total_skus:,}"
    )


with c2:

    st.metric(
        "Current Stock",
        f"{total_stock:,.0f}"
    )


with c3:

    st.metric(
        "6-Week Forecast",
        f"{total_forecast:,.0f}"
    )


with c4:

    st.metric(
        "Excess Inventory",
        f"₹{total_excess_value:,.0f}"
    )


with c5:

    st.metric(
        "Excess Stock %",
        f"{excess_percentage:.1f}%"
    )


st.write("")


# ============================================================
# RISK OVERVIEW
# ============================================================

reorder_count = len(
    filtered_inventory[
        filtered_inventory["decision"]
        == "Reorder Now"
    ]
)


markdown_count = len(
    filtered_inventory[
        filtered_inventory["decision"]
        == "Markdown/Clear"
    ]
)


watch_count = len(
    filtered_inventory[
        filtered_inventory["decision"]
        == "Watch/Volatile"
    ]
)


healthy_count = len(
    filtered_inventory[
        filtered_inventory["decision"]
        == "Healthy"
    ]
)


st.markdown(
    '<div class="section-title">'
    '⚠️ Inventory Risk Overview'
    '</div>',
    unsafe_allow_html=True
)


r1, r2, r3, r4 = st.columns(4)


with r1:

    st.metric(
        "🔴 Reorder Now",
        reorder_count
    )


with r2:

    st.metric(
        "🟠 Markdown / Clear",
        markdown_count
    )


with r3:

    st.metric(
        "🟡 Watch / Volatile",
        watch_count
    )


with r4:

    st.metric(
        "🟢 Healthy",
        healthy_count
    )


st.divider()


# ============================================================
# MODEL PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🤖 Forecast Model Performance'
    '</div>',
    unsafe_allow_html=True
)


st.caption(
    "Primary validation uses three rolling-origin six-week "
    "validation windows. The latest six-week holdout is shown "
    "as an additional sanity check."
)


p1, p2, p3 = st.columns(3)


with p1:

    st.metric(
        "Rolling-CV Model WAPE",
        "27.48%"
    )


with p2:

    st.metric(
        "Seasonal-Naive WAPE",
        "38.35%"
    )


with p3:

    st.metric(
        "Relative Improvement",
        "28.35%"
    )


p4, p5, p6 = st.columns(3)


with p4:

    st.metric(
        "Rolling-CV Model Bias",
        "+0.19%"
    )


with p5:

    st.metric(
        "Latest Holdout WAPE",
        "32.88%"
    )


with p6:

    st.metric(
        "Latest Holdout Bias",
        "+9.32%"
    )


st.success(
    "Gradient Boosting beats the seasonal-naive baseline "
    "across all three rolling-origin validation windows."
)


# ============================================================
# ROLLING VALIDATION CHART
# ============================================================

cv_data = pd.DataFrame(
    {
        "Validation Origin": [
            "2025-06-16",
            "2025-07-14",
            "2025-08-11"
        ],
        "Gradient Boosting": [
            25.93,
            27.07,
            29.42
        ],
        "Seasonal Naive": [
            37.30,
            38.26,
            39.49
        ]
    }
)


fig_cv = px.bar(
    cv_data,
    x="Validation Origin",
    y=[
        "Gradient Boosting",
        "Seasonal Naive"
    ],
    barmode="group",
    title="Rolling-Origin WAPE Comparison",
    labels={
        "value": "WAPE (%)",
        "variable": "Model"
    }
)


fig_cv.update_layout(
    height=400,
    yaxis_title="WAPE (%)",
    xaxis_title="Validation Origin"
)


st.plotly_chart(
    fig_cv,
    use_container_width=True
)


st.divider()


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📈 Category Inventory Analysis'
    '</div>',
    unsafe_allow_html=True
)


if len(filtered_inventory) > 0:

    category_summary = (
        filtered_inventory
        .groupby(
            "category",
            as_index=False
        )
        .agg(
            stock_on_hand=(
                "stock_on_hand",
                "sum"
            ),
            forecast_6_week_demand=(
                "forecast_6_week_demand",
                "sum"
            ),
            excess_units=(
                "excess_units",
                "sum"
            ),
            excess_value=(
                "excess_value",
                "sum"
            )
        )
    )


    col_chart1, col_chart2 = st.columns(2)


    with col_chart1:

        fig_category = px.bar(
            category_summary,
            x="category",
            y="excess_value",
            title="Excess Inventory Value by Category",
            labels={
                "category": "Category",
                "excess_value":
                    "Excess Value (₹)"
            },
            text_auto=".2s"
        )

        fig_category.update_layout(
            height=450,
            showlegend=False
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )


    with col_chart2:

        fig_stock = px.bar(
            category_summary,
            x="category",
            y=[
                "stock_on_hand",
                "forecast_6_week_demand"
            ],
            barmode="group",
            title="Current Stock vs 6-Week Forecast",
            labels={
                "value": "Units",
                "variable": "Metric",
                "category": "Category"
            }
        )

        fig_stock.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_stock,
            use_container_width=True
        )

else:

    st.warning(
        "No category data matches the selected filters."
    )


st.divider()


# ============================================================
# HISTORICAL DEMAND + FUTURE FORECAST
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📉 Historical Demand & Future Forecast'
    '</div>',
    unsafe_allow_html=True
)


st.caption(
    "Historical weekly demand is shown together with the "
    "six-week forecast. Use the SKU selector below to inspect "
    "individual demand patterns."
)


# ------------------------------------------------------------
# Historical demand filtered to selected category
# ------------------------------------------------------------

historical_filtered = weekly[
    weekly["sku_id"].isin(
        filtered_inventory["sku_id"]
    )
].copy()


historical_summary = (
    historical_filtered
    .groupby(
        "week",
        as_index=False
    )
    .agg(
        actual_demand=(
            "demand",
            "sum"
        )
    )
)


# ------------------------------------------------------------
# Future forecast filtered to selected category
# ------------------------------------------------------------

future_filtered = forecast[
    forecast["sku_id"].isin(
        filtered_inventory["sku_id"]
    )
].copy()


future_summary = (
    future_filtered
    .groupby(
        "week",
        as_index=False
    )
    .agg(
        forecast_demand=(
            "forecast_demand",
            "sum"
        )
    )
)


# ------------------------------------------------------------
# Combined chart
# ------------------------------------------------------------

fig_history = go.Figure()


fig_history.add_trace(
    go.Scatter(
        x=historical_summary["week"],
        y=historical_summary["actual_demand"],
        mode="lines",
        name="Historical Actual Demand"
    )
)


fig_history.add_trace(
    go.Scatter(
        x=future_summary["week"],
        y=future_summary["forecast_demand"],
        mode="lines+markers",
        name="6-Week Forecast"
    )
)


fig_history.update_layout(
    title="Weekly Demand History and Future Forecast",
    xaxis_title="Week",
    yaxis_title="Demand Units",
    height=500,
    hovermode="x unified"
)


st.plotly_chart(
    fig_history,
    use_container_width=True
)


st.divider()


# ============================================================
# SIX WEEK FORECAST
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📅 Six-Week Demand Forecast'
    '</div>',
    unsafe_allow_html=True
)


weekly_forecast = (
    future_filtered
    .groupby(
        "week",
        as_index=False
    )
    .agg(
        forecast_demand=(
            "forecast_demand",
            "sum"
        )
    )
)


fig_forecast = px.line(
    weekly_forecast,
    x="week",
    y="forecast_demand",
    markers=True,
    title="Total Forecasted Demand — Next 6 Weeks",
    labels={
        "week": "Week",
        "forecast_demand":
            "Forecast Demand"
    }
)


fig_forecast.update_layout(
    height=450,
    hovermode="x unified"
)


st.plotly_chart(
    fig_forecast,
    use_container_width=True
)


st.divider()


# ============================================================
# PRIORITY ACTIONS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🚨 Priority Inventory Actions'
    '</div>',
    unsafe_allow_html=True
)


if len(filtered_inventory) > 0:

    priority_data = (
        filtered_inventory
        .sort_values(
            "priority_rank",
            ascending=True
        )
        .head(10)
    )


    priority_columns = [
        "priority_rank",
        "sku_id",
        "sku_name",
        "category",
        "stock_on_hand",
        "forecast_6_week_demand",
        "excess_units",
        "excess_value",
        "forecast_cv",
        "decision"
    ]


    st.dataframe(
        priority_data[
            priority_columns
        ],
        use_container_width=True,
        hide_index=True,
        column_config={

            "priority_rank":
                "Priority",

            "sku_id":
                "SKU ID",

            "sku_name":
                "SKU Name",

            "category":
                "Category",

            "stock_on_hand":
                st.column_config.NumberColumn(
                    "Current Stock",
                    format="%.0f"
                ),

            "forecast_6_week_demand":
                st.column_config.NumberColumn(
                    "6W Forecast",
                    format="%.0f"
                ),

            "excess_units":
                st.column_config.NumberColumn(
                    "Excess Units",
                    format="%.0f"
                ),

            "excess_value":
                st.column_config.NumberColumn(
                    "Excess Value",
                    format="₹%.0f"
                ),

            "forecast_cv":
                st.column_config.NumberColumn(
                    "Forecast CV",
                    format="%.3f"
                ),

            "decision":
                "Action"
        }
    )

else:

    st.warning(
        "No priority actions match the selected filters."
    )


st.divider()


# ============================================================
# SKU LEVEL INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🔍 SKU-Level Intelligence'
    '</div>',
    unsafe_allow_html=True
)


if len(filtered_inventory) > 0:

    sku_options = (
        filtered_inventory[
            "sku_id"
        ]
        .sort_values()
        .tolist()
    )


    selected_sku = st.selectbox(
        "Select SKU to analyze",
        sku_options
    )


    sku_info = filtered_inventory[
        filtered_inventory[
            "sku_id"
        ] == selected_sku
    ].iloc[0]


    sku_forecast = forecast[
        forecast[
            "sku_id"
        ] == selected_sku
    ].sort_values("week")


    sku_history = weekly[
        weekly[
            "sku_id"
        ] == selected_sku
    ].sort_values("week")


    s1, s2, s3, s4, s5 = st.columns(5)


    with s1:

        st.metric(
            "SKU",
            str(selected_sku)
        )


    with s2:

        st.metric(
            "Current Stock",
            f"{sku_info['stock_on_hand']:,.0f}"
        )


    with s3:

        st.metric(
            "6W Forecast",
            f"{sku_info['forecast_6_week_demand']:,.0f}"
        )


    with s4:

        st.metric(
            "Coverage",
            f"{sku_info['coverage_weeks']:.1f} weeks"
        )


    with s5:

        st.metric(
            "Decision",
            str(sku_info["decision"])
        )


    # --------------------------------------------------------
    # SKU historical + forecast chart
    # --------------------------------------------------------

    fig_sku = go.Figure()


    fig_sku.add_trace(
        go.Scatter(
            x=sku_history["week"],
            y=sku_history["demand"],
            mode="lines",
            name="Historical Demand"
        )
    )


    fig_sku.add_trace(
        go.Scatter(
            x=sku_forecast["week"],
            y=sku_forecast[
                "forecast_demand"
            ],
            mode="lines+markers",
            name="Forecast"
        )
    )


    fig_sku.update_layout(
        height=450,
        title=(
            f"Demand History & Forecast — "
            f"SKU {selected_sku}"
        ),
        xaxis_title="Week",
        yaxis_title="Demand",
        hovermode="x unified"
    )


    st.plotly_chart(
        fig_sku,
        use_container_width=True
    )


    # --------------------------------------------------------
    # SKU business information
    # --------------------------------------------------------

    st.write(
        f"**Product:** {sku_info['sku_name']}"
    )

    st.write(
        f"**Category:** {sku_info['category']} "
        f"| **Subcategory:** {sku_info['subcategory']} "
        f"| **Brand:** {sku_info['brand']}"
    )


    a1, a2, a3 = st.columns(3)


    with a1:

        st.metric(
            "Excess Units",
            f"{sku_info['excess_units']:,.0f}"
        )


    with a2:

        st.metric(
            "Excess Value",
            f"₹{sku_info['excess_value']:,.0f}"
        )


    with a3:

        st.metric(
            "Forecast Volatility",
            f"{sku_info['forecast_cv']:.3f}"
        )


else:

    st.warning(
        "No SKUs match the selected filters. "
        "Please change the category or risk decision."
    )


st.divider()


# ============================================================
# INVENTORY RISK TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📋 Inventory Risk Table'
    '</div>',
    unsafe_allow_html=True
)


display_columns = [
    "sku_id",
    "sku_name",
    "category",
    "stock_on_hand",
    "forecast_6_week_demand",
    "avg_weekly_forecast",
    "coverage_weeks",
    "excess_units",
    "excess_value",
    "forecast_cv",
    "decision",
    "priority_rank"
]


if len(filtered_inventory) > 0:

    st.dataframe(
        filtered_inventory[
            display_columns
        ].sort_values(
            "priority_rank"
        ),
        use_container_width=True,
        hide_index=True,
        column_config={

            "sku_id":
                "SKU ID",

            "sku_name":
                "SKU Name",

            "category":
                "Category",

            "stock_on_hand":
                st.column_config.NumberColumn(
                    "Stock",
                    format="%.0f"
                ),

            "forecast_6_week_demand":
                st.column_config.NumberColumn(
                    "6W Forecast",
                    format="%.0f"
                ),

            "avg_weekly_forecast":
                st.column_config.NumberColumn(
                    "Avg Weekly Forecast",
                    format="%.1f"
                ),

            "coverage_weeks":
                st.column_config.NumberColumn(
                    "Coverage",
                    format="%.1f weeks"
                ),

            "excess_units":
                st.column_config.NumberColumn(
                    "Excess Units",
                    format="%.0f"
                ),

            "excess_value":
                st.column_config.NumberColumn(
                    "Excess Value",
                    format="₹%.0f"
                ),

            "forecast_cv":
                st.column_config.NumberColumn(
                    "CV",
                    format="%.3f"
                ),

            "decision":
                "Risk Decision",

            "priority_rank":
                "Priority"
        }
    )

else:

    st.warning(
        "No inventory records match the selected filters."
    )


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.divider()


st.markdown(
    '<div class="section-title">'
    '💡 Key Business Insights'
    '</div>',
    unsafe_allow_html=True
)


if len(filtered_inventory) > 0:

    # --------------------------------------------------------
    # Highest impact category
    # --------------------------------------------------------

    category_impact = (
        filtered_inventory
        .groupby("category")[
            "excess_value"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )


    highest_category = (
        category_impact.index[0]
    )


    highest_category_value = (
        category_impact.iloc[0]
    )


    # --------------------------------------------------------
    # Priority SKU
    # --------------------------------------------------------

    top_sku = (
        filtered_inventory
        .sort_values(
            "priority_rank"
        )
        .iloc[0]
    )


    i1, i2, i3 = st.columns(3)


    with i1:

        st.info(
            f"""
**High Excess Inventory**

The filtered portfolio contains approximately
**₹{total_excess_value:,.0f}**
of excess inventory value.

The primary opportunity is to reduce
working-capital exposure.
"""
        )


    with i2:

        st.info(
            f"""
**Highest-Impact Category**

**{highest_category}**
has the largest excess inventory
value in the current selection:

**₹{highest_category_value:,.0f}**
"""
        )


    with i3:

        st.info(
            f"""
**Top Priority SKU**

SKU **{int(top_sku['sku_id'])}**
is currently ranked **#1** within
the selected portfolio.

Recommended action:

**{top_sku['decision']}**
"""
        )


else:

    st.info(
        "Select a category or risk decision with available "
        "inventory records to view business insights."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "PROJECT FORESIGHT | "
    "AI-Powered Demand & Inventory Intelligence | "
    "NorthBay Living | "
    "Forecast Horizon: 6 Weeks"
)