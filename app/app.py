import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

st.markdown("""
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

.kpi-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

.kpi-label {
    font-size: 14px;
    color: #6b7280;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    margin-top: 5px;
}

.info-box {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================

inventory = pd.read_csv(
    r"D:\FORESIGHT\data\final_inventory_risk.csv"
)

forecast = pd.read_csv(
    r"D:\FORESIGHT\data\final_6_week_forecast.csv"
)

forecast["week"] = pd.to_datetime(forecast["week"])

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
    "**NorthBay Living** | Demand Forecasting • Inventory Risk • Decision Intelligence"
)

st.divider()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Dashboard Controls")

st.sidebar.markdown(
    "Use the filters below to explore inventory risk."
)

categories = ["All"] + sorted(
    inventory["category"].dropna().unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "📂 Category",
    categories
)

decisions = ["All"] + sorted(
    inventory["decision"].dropna().unique().tolist()
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
        filtered_inventory["category"] == selected_category
    ]

if selected_decision != "All":
    filtered_inventory = filtered_inventory[
        filtered_inventory["decision"] == selected_decision
    ]

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_skus = len(filtered_inventory)

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
    total_excess_units / total_stock * 100
    if total_stock > 0
    else 0
)

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📊 Executive Summary</div>',
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
# RISK COUNTS
# ============================================================

reorder_count = len(
    filtered_inventory[
        filtered_inventory["decision"] == "Reorder Now"
    ]
)

markdown_count = len(
    filtered_inventory[
        filtered_inventory["decision"] == "Markdown/Clear"
    ]
)

watch_count = len(
    filtered_inventory[
        filtered_inventory["decision"] == "Watch/Volatile"
    ]
)

healthy_count = len(
    filtered_inventory[
        filtered_inventory["decision"] == "Healthy"
    ]
)

st.markdown(
    '<div class="section-title">⚠️ Inventory Risk Overview</div>',
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
# CATEGORY ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Category Inventory Analysis</div>',
    unsafe_allow_html=True
)

category_summary = (
    filtered_inventory
    .groupby("category", as_index=False)
    .agg(
        stock_on_hand=("stock_on_hand", "sum"),
        forecast_6_week_demand=(
            "forecast_6_week_demand",
            "sum"
        ),
        excess_units=("excess_units", "sum"),
        excess_value=("excess_value", "sum")
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
            "excess_value": "Excess Value (₹)"
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

# ============================================================
# SIX WEEK FORECAST
# ============================================================

st.markdown(
    '<div class="section-title">📅 Six-Week Demand Forecast</div>',
    unsafe_allow_html=True
)

forecast_filtered = forecast[
    forecast["sku_id"].isin(
        filtered_inventory["sku_id"]
    )
]

weekly_forecast = (
    forecast_filtered
    .groupby("week", as_index=False)
    .agg(
        forecast_demand=("forecast_demand", "sum")
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
        "forecast_demand": "Forecast Demand"
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
    '<div class="section-title">🚨 Priority Inventory Actions</div>',
    unsafe_allow_html=True
)

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
    priority_data[priority_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        "priority_rank": "Priority",
        "sku_id": "SKU ID",
        "sku_name": "SKU Name",
        "category": "Category",
        "stock_on_hand": st.column_config.NumberColumn(
            "Current Stock",
            format="%.0f"
        ),
        "forecast_6_week_demand": st.column_config.NumberColumn(
            "6W Forecast",
            format="%.0f"
        ),
        "excess_units": st.column_config.NumberColumn(
            "Excess Units",
            format="%.0f"
        ),
        "excess_value": st.column_config.NumberColumn(
            "Excess Value",
            format="₹%.0f"
        ),
        "forecast_cv": st.column_config.NumberColumn(
            "Forecast CV",
            format="%.3f"
        ),
        "decision": "Action"
    }
)

st.divider()

# ============================================================
# SKU DETAIL
# ============================================================

st.markdown(
    '<div class="section-title">🔍 SKU-Level Intelligence</div>',
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
        filtered_inventory["sku_id"] == selected_sku
    ].iloc[0]

    sku_forecast = forecast[
        forecast["sku_id"] == selected_sku
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

    fig_sku = px.line(
        sku_forecast,
        x="week",
        y="forecast_demand",
        markers=True,
        title=f"Demand Forecast — SKU {selected_sku}",
        labels={
            "week": "Week",
            "forecast_demand": "Forecast Demand"
        }
    )

    fig_sku.update_layout(
        height=400,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_sku,
        use_container_width=True
    )

# ============================================================
# INVENTORY RISK TABLE
# ============================================================

st.markdown(
    '<div class="section-title">📋 Inventory Risk Table</div>',
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

st.dataframe(
    filtered_inventory[
        display_columns
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "sku_id": "SKU ID",
        "sku_name": "SKU Name",
        "category": "Category",
        "stock_on_hand": st.column_config.NumberColumn(
            "Stock",
            format="%.0f"
        ),
        "forecast_6_week_demand": st.column_config.NumberColumn(
            "6W Forecast",
            format="%.0f"
        ),
        "avg_weekly_forecast": st.column_config.NumberColumn(
            "Avg Weekly Forecast",
            format="%.1f"
        ),
        "coverage_weeks": st.column_config.NumberColumn(
            "Coverage",
            format="%.1f weeks"
        ),
        "excess_units": st.column_config.NumberColumn(
            "Excess Units",
            format="%.0f"
        ),
        "excess_value": st.column_config.NumberColumn(
            "Excess Value",
            format="₹%.0f"
        ),
        "forecast_cv": st.column_config.NumberColumn(
            "CV",
            format="%.3f"
        ),
        "decision": "Risk Decision",
        "priority_rank": "Priority"
    }
)

# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">💡 Key Business Insights</div>',
    unsafe_allow_html=True
)

i1, i2, i3 = st.columns(3)

with i1:
    st.info(
        """
        **High Excess Inventory**

        The current inventory position is substantially
        higher than the six-week forecast demand, creating
        a significant working-capital exposure.
        """
    )

with i2:
    st.info(
        """
        **Electronics Has Highest Impact**

        Electronics contributes the largest share of
        excess inventory value and should receive
        management attention first.
        """
    )

with i3:
    st.info(
        """
        **Markdown Is the Main Action**

        Most SKUs are classified as Markdown/Clear,
        while a smaller group is Watch/Volatile.
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "PROJECT FORESIGHT | AI-Powered Demand & Inventory Intelligence | "
    "NorthBay Living | Forecast Horizon: 6 Weeks"
)