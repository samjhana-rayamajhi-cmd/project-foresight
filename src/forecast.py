import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor


# ============================================================
# PROJECT FORESIGHT - FORECAST PIPELINE
# ============================================================

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

WEEKLY_FILE = DATA_DIR / "analysis_ready_weekly.csv"
OUTPUT_FILE = DATA_DIR / "final_6_week_forecast.csv"


# ============================================================
# FEATURE COLUMNS
# ============================================================

FEATURE_COLUMNS = [
    "lag_1",
    "lag_2",
    "lag_4",
    "lag_8",
    "lag_13",
    "lag_26",
    "lag_52",
    "rolling_mean_4",
    "rolling_mean_8",
    "rolling_mean_13",
    "week_number",
    "month",
    "quarter",
    "year",
    "promo_flag",
    "promo_discount",
    "promo_count",
]

# Final model includes SKU identity
IMPROVED_FEATURE_COLUMNS = FEATURE_COLUMNS + ["sku_id"]


# ============================================================
# MODEL CREATION
# ============================================================

def create_model():

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )

    return model


# ============================================================
# FEATURE CREATION
# ============================================================

def create_features(df):
    """
    Create leakage-safe forecasting features.

    Features:
    - Historical demand lags
    - Leakage-safe rolling means
    - Calendar features
    - Promotion features
    """

    df = df.copy()

    # Ensure week is datetime
    df["week"] = pd.to_datetime(df["week"])

    # Sort chronologically within each SKU
    df = (
        df
        .sort_values(["sku_id", "week"])
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Lag features
    # --------------------------------------------------------

    for lag in [1, 2, 4, 8, 13, 26, 52]:

        df[f"lag_{lag}"] = (
            df
            .groupby("sku_id")["demand"]
            .shift(lag)
        )

    # --------------------------------------------------------
    # Rolling features
    # Use shift(1) to avoid data leakage
    # --------------------------------------------------------

    for window in [4, 8, 13]:

        df[f"rolling_mean_{window}"] = (
            df
            .groupby("sku_id")["demand"]
            .transform(
                lambda x:
                x.shift(1)
                .rolling(window)
                .mean()
            )
        )

    # --------------------------------------------------------
    # Calendar features
    # --------------------------------------------------------

    df["week_number"] = (
        df["week"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    df["month"] = df["week"].dt.month

    df["quarter"] = df["week"].dt.quarter

    df["year"] = df["week"].dt.year

    return df


# ============================================================
# METRIC FUNCTIONS
# ============================================================

def calculate_wape(actual, predicted):

    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    denominator = np.sum(np.abs(actual))

    if denominator == 0:
        return np.nan

    return (
        np.sum(np.abs(actual - predicted))
        / denominator
    ) * 100


def calculate_bias(actual, predicted):

    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    denominator = np.sum(np.abs(actual))

    if denominator == 0:
        return np.nan

    return (
        np.sum(predicted - actual)
        / denominator
    ) * 100


# ============================================================
# SEASONAL-NAIVE PREDICTION
# ============================================================

def create_seasonal_naive_predictions(
    weekly_data,
    validation_data
):
    """
    Seasonal-naive forecast:
    demand from the same SKU 52 weeks earlier.
    """

    historical = weekly_data[
        ["week", "sku_id", "demand"]
    ].copy()

    # The value 52 weeks before the validation week
    historical["forecast_week"] = (
        historical["week"]
        + pd.Timedelta(weeks=52)
    )

    historical = historical.rename(
        columns={
            "demand": "seasonal_naive"
        }
    )

    naive = validation_data.merge(
        historical[
            [
                "forecast_week",
                "sku_id",
                "seasonal_naive"
            ]
        ],
        left_on=["week", "sku_id"],
        right_on=["forecast_week", "sku_id"],
        how="left"
    )

    return naive["seasonal_naive"].values


# ============================================================
# ROLLING-ORIGIN CROSS-VALIDATION
# ============================================================

def rolling_origin_validation(
    model_ready,
    weekly_data
):
    """
    Rolling-origin validation.

    Each origin:
    - Uses only data available before the origin
    - Predicts the following 6 weeks
    - Compares Gradient Boosting with seasonal-naive
    """

    print("\n" + "=" * 60)
    print("ROLLING-ORIGIN CROSS-VALIDATION")
    print("=" * 60)

    # Validation origins from the forecasting notebook
    origins = [
        pd.Timestamp("2025-06-16"),
        pd.Timestamp("2025-07-14"),
        pd.Timestamp("2025-08-11")
    ]

    results = []

    for origin in origins:

        # ----------------------------------------------------
        # Six validation weeks after origin
        # ----------------------------------------------------

        validation_weeks = pd.date_range(
            start=origin + pd.Timedelta(weeks=1),
            periods=6,
            freq="7D"
        )

        # ----------------------------------------------------
        # Training data
        # Only information available before validation
        # ----------------------------------------------------

        train_data = model_ready[
            model_ready["week"] <= origin
        ].copy()

        # ----------------------------------------------------
        # Validation data
        # ----------------------------------------------------

        validation_data = model_ready[
            model_ready["week"].isin(validation_weeks)
        ].copy()

        if validation_data.empty:

            print(
                f"\nSkipping origin {origin.date()} "
                f"- validation data unavailable."
            )

            continue

        print("\n" + "-" * 60)

        print(
            f"Validation Origin: {origin.date()}"
        )

        print(
            "Validation Period:",
            validation_weeks.min().date(),
            "to",
            validation_weeks.max().date()
        )

        print(
            "Training rows:",
            len(train_data)
        )

        print(
            "Validation rows:",
            len(validation_data)
        )

        # ----------------------------------------------------
        # Train Gradient Boosting
        # ----------------------------------------------------

        cv_model = create_model()

        cv_model.fit(
            train_data[IMPROVED_FEATURE_COLUMNS],
            train_data["demand"]
        )

        # ----------------------------------------------------
        # Gradient Boosting predictions
        # ----------------------------------------------------

        model_predictions = cv_model.predict(
            validation_data[
                IMPROVED_FEATURE_COLUMNS
            ]
        )

        model_predictions = np.maximum(
            model_predictions,
            0
        )

        actual = validation_data["demand"].values

        model_wape = calculate_wape(
            actual,
            model_predictions
        )

        model_bias = calculate_bias(
            actual,
            model_predictions
        )

        # ----------------------------------------------------
        # Seasonal Naive predictions
        # ----------------------------------------------------

        naive_predictions = (
            create_seasonal_naive_predictions(
                weekly_data,
                validation_data
            )
        )

        valid_naive = ~pd.isna(
            naive_predictions
        )

        naive_actual = actual[
            valid_naive
        ]

        naive_predictions_valid = (
            naive_predictions[
                valid_naive
            ]
        )

        naive_wape = calculate_wape(
            naive_actual,
            naive_predictions_valid
        )

        naive_bias = calculate_bias(
            naive_actual,
            naive_predictions_valid
        )

        # ----------------------------------------------------
        # Print results
        # ----------------------------------------------------

        print(
            f"Gradient Boosting WAPE: "
            f"{model_wape:.2f}%"
        )

        print(
            f"Gradient Boosting Bias: "
            f"{model_bias:+.2f}%"
        )

        print(
            f"Seasonal Naive WAPE: "
            f"{naive_wape:.2f}%"
        )

        print(
            f"Seasonal Naive Bias: "
            f"{naive_bias:+.2f}%"
        )

        results.append(
            {
                "origin": origin,
                "model_wape": model_wape,
                "model_bias": model_bias,
                "naive_wape": naive_wape,
                "naive_bias": naive_bias
            }
        )

    # ========================================================
    # CV SUMMARY
    # ========================================================

    results_df = pd.DataFrame(results)

    if results_df.empty:

        print(
            "\nNo rolling-origin validation results available."
        )

        return results_df

    print("\n" + "=" * 60)
    print("ROLLING-ORIGIN SUMMARY")
    print("=" * 60)

    print("\nValidation Results:")

    print(
        results_df.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Average metrics
    # --------------------------------------------------------

    avg_model_wape = (
        results_df["model_wape"]
        .mean()
    )

    avg_model_bias = (
        results_df["model_bias"]
        .mean()
    )

    avg_naive_wape = (
        results_df["naive_wape"]
        .mean()
    )

    avg_naive_bias = (
        results_df["naive_bias"]
        .mean()
    )

    # Relative improvement
    relative_improvement = (
        (
            avg_naive_wape
            - avg_model_wape
        )
        / avg_naive_wape
    ) * 100

    print("\nAverage Results")
    print("----------------")

    print(
        f"Gradient Boosting WAPE: "
        f"{avg_model_wape:.2f}%"
    )

    print(
        f"Gradient Boosting Bias: "
        f"{avg_model_bias:+.2f}%"
    )

    print(
        f"Seasonal Naive WAPE: "
        f"{avg_naive_wape:.2f}%"
    )

    print(
        f"Seasonal Naive Bias: "
        f"{avg_naive_bias:+.2f}%"
    )

    print(
        f"Relative WAPE Improvement: "
        f"{relative_improvement:.2f}%"
    )

    # --------------------------------------------------------
    # Winner
    # --------------------------------------------------------

    if avg_model_wape < avg_naive_wape:

        print(
            "\nResult: Gradient Boosting "
            "beats the seasonal-naive baseline."
        )

    else:

        print(
            "\nResult: Seasonal-naive "
            "beats Gradient Boosting."
        )

    return results_df


# ============================================================
# MAIN FORECASTING PROCESS
# ============================================================

def main():

    print("=" * 60)
    print("PROJECT FORESIGHT - FORECAST PIPELINE")
    print("=" * 60)

    # ========================================================
    # 1. LOAD DATA
    # ========================================================

    print(
        "\n[1/7] Loading weekly dataset..."
    )

    weekly_data = pd.read_csv(
        WEEKLY_FILE
    )

    weekly_data["week"] = pd.to_datetime(
        weekly_data["week"]
    )

    print(
        "Weekly data shape:",
        weekly_data.shape
    )

    print(
        "Historical weeks:",
        weekly_data["week"].min().date(),
        "to",
        weekly_data["week"].max().date()
    )

    print(
        "Number of SKUs:",
        weekly_data["sku_id"].nunique()
    )

    # ========================================================
    # 2. CREATE FEATURES
    # ========================================================

    print(
        "\n[2/7] Creating forecasting features..."
    )

    model_data = create_features(
        weekly_data
    )

    print(
        "Feature dataset shape:",
        model_data.shape
    )

    # Remove rows where lag/rolling features
    # are unavailable

    model_ready = (
        model_data
        .dropna(
            subset=IMPROVED_FEATURE_COLUMNS
        )
        .copy()
    )

    print(
        "Model-ready shape:",
        model_ready.shape
    )

    # ========================================================
    # ROLLING-ORIGIN VALIDATION
    # ========================================================

    cv_results = rolling_origin_validation(
        model_ready,
        weekly_data
    )

    # ========================================================
    # 3. TIME-BASED TRAIN/TEST SPLIT
    # ========================================================

    print(
        "\n[3/7] Creating time-based train/test split..."
    )

    test_weeks = (
        sorted(
            model_ready["week"].unique()
        )[-6:]
    )

    train_data = model_ready[
        ~model_ready["week"].isin(
            test_weeks
        )
    ].copy()

    test_data = model_ready[
        model_ready["week"].isin(
            test_weeks
        )
    ].copy()

    print(
        "Training shape:",
        train_data.shape
    )

    print(
        "Test shape:",
        test_data.shape
    )

    print("\nTest weeks:")

    for week in test_weeks:

        print(
            pd.Timestamp(week).date()
        )

    # ========================================================
    # 4. TRAIN MODEL
    # ========================================================

    print(
        "\n[4/7] Training final Gradient Boosting model..."
    )

    X_train = train_data[
        IMPROVED_FEATURE_COLUMNS
    ]

    y_train = train_data[
        "demand"
    ]

    X_test = test_data[
        IMPROVED_FEATURE_COLUMNS
    ]

    y_test = test_data[
        "demand"
    ]

    model = create_model()

    model.fit(
        X_train,
        y_train
    )

    print(
        "Model trained successfully!"
    )

    print(
        "Training rows:",
        len(X_train)
    )

    print(
        "Features:",
        len(
            IMPROVED_FEATURE_COLUMNS
        )
    )

    # ========================================================
    # 5. HOLDOUT EVALUATION
    # ========================================================

    print(
        "\n[5/7] Evaluating model..."
    )

    predictions = model.predict(
        X_test
    )

    predictions = np.maximum(
        predictions,
        0
    )

    actual = y_test.values

    wape = calculate_wape(
        actual,
        predictions
    )

    bias = calculate_bias(
        actual,
        predictions
    )

    print(
        "\nFinal 6-Week Holdout Performance"
    )

    print(
        "---------------------------------"
    )

    print(
        f"WAPE: {wape:.2f}%"
    )

    print(
        f"Bias: {bias:+.2f}%"
    )

    # ========================================================
    # HOLDOUT SEASONAL-NAIVE BASELINE
    # ========================================================

    naive_holdout = (
        create_seasonal_naive_predictions(
            weekly_data,
            test_data
        )
    )

    valid_naive = ~pd.isna(
        naive_holdout
    )

    if valid_naive.any():

        naive_holdout_actual = (
            actual[valid_naive]
        )

        naive_holdout_predictions = (
            naive_holdout[valid_naive]
        )

        holdout_naive_wape = calculate_wape(
            naive_holdout_actual,
            naive_holdout_predictions
        )

        holdout_naive_bias = calculate_bias(
            naive_holdout_actual,
            naive_holdout_predictions
        )

        print(
            f"Seasonal Naive WAPE: "
            f"{holdout_naive_wape:.2f}%"
        )

        print(
            f"Seasonal Naive Bias: "
            f"{holdout_naive_bias:+.2f}%"
        )

    # ========================================================
    # 6. TRAIN FINAL MODEL ON ALL HISTORY
    # ========================================================

    print(
        "\n[6/7] Training final model "
        "on all available history..."
    )

    X_full = model_ready[
        IMPROVED_FEATURE_COLUMNS
    ]

    y_full = model_ready[
        "demand"
    ]

    final_model = create_model()

    final_model.fit(
        X_full,
        y_full
    )

    print(
        "Final model trained!"
    )

    print(
        "Full training rows:",
        len(X_full)
    )

    # ========================================================
    # 7. RECURSIVE 6-WEEK FORECAST
    # ========================================================

    print(
        "\n[7/7] Generating recursive "
        "6-week forecast..."
    )

    latest_week = (
        weekly_data["week"].max()
    )

    future_weeks = pd.date_range(
        start=(
            latest_week
            + pd.Timedelta(weeks=1)
        ),
        periods=6,
        freq="7D"
    )

    print(
        "Latest historical week:",
        latest_week.date()
    )

    print("\nFuture forecast weeks:")

    for week in future_weeks:

        print(
            week.date()
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # Use the full historical dataset
    # for recursive forecasting.
    # --------------------------------------------------------

    history_recursive = (
        weekly_data[
            [
                "week",
                "sku_id",
                "demand"
            ]
        ]
        .copy()
        .sort_values(
            ["sku_id", "week"]
        )
        .reset_index(drop=True)
    )

    all_skus = (
        weekly_data["sku_id"]
        .unique()
    )

    forecast_results = []

    # ========================================================
    # RECURSIVE FORECAST LOOP
    # ========================================================

    for future_week in future_weeks:

        print(
            f"\nForecasting week: "
            f"{future_week.date()}"
        )

        week_predictions = []

        for sku in all_skus:

            # ------------------------------------------------
            # Get SKU history
            # ------------------------------------------------

            sku_history = (
                history_recursive[
                    history_recursive[
                        "sku_id"
                    ] == sku
                ]
                .sort_values("week")
            )

            demand_history = (
                sku_history[
                    "demand"
                ].values
            )

            # ------------------------------------------------
            # Lag features
            # ------------------------------------------------

            lag_1 = demand_history[-1]
            lag_2 = demand_history[-2]
            lag_4 = demand_history[-4]
            lag_8 = demand_history[-8]
            lag_13 = demand_history[-13]
            lag_26 = demand_history[-26]
            lag_52 = demand_history[-52]

            # ------------------------------------------------
            # Rolling features
            # ------------------------------------------------

            rolling_mean_4 = np.mean(
                demand_history[-4:]
            )

            rolling_mean_8 = np.mean(
                demand_history[-8:]
            )

            rolling_mean_13 = np.mean(
                demand_history[-13:]
            )

            # ------------------------------------------------
            # Calendar features
            # ------------------------------------------------

            week_number = int(
                future_week
                .isocalendar()
                .week
            )

            month = future_week.month

            quarter = future_week.quarter

            year = future_week.year

            # ------------------------------------------------
            # Future promotion features
            #
            # The forecast period has no promotions.
            # ------------------------------------------------

            promo_flag = 0
            promo_discount = 0
            promo_count = 0

            # ------------------------------------------------
            # Model input
            # ------------------------------------------------

            X_future = pd.DataFrame(
                [
                    {
                        "lag_1": lag_1,
                        "lag_2": lag_2,
                        "lag_4": lag_4,
                        "lag_8": lag_8,
                        "lag_13": lag_13,
                        "lag_26": lag_26,
                        "lag_52": lag_52,

                        "rolling_mean_4":
                            rolling_mean_4,

                        "rolling_mean_8":
                            rolling_mean_8,

                        "rolling_mean_13":
                            rolling_mean_13,

                        "week_number":
                            week_number,

                        "month":
                            month,

                        "quarter":
                            quarter,

                        "year":
                            year,

                        "promo_flag":
                            promo_flag,

                        "promo_discount":
                            promo_discount,

                        "promo_count":
                            promo_count,

                        "sku_id":
                            sku
                    }
                ]
            )

            # ------------------------------------------------
            # Predict
            # ------------------------------------------------

            prediction = (
                final_model.predict(
                    X_future[
                        IMPROVED_FEATURE_COLUMNS
                    ]
                )[0]
            )

            # Ensure non-negative demand
            prediction = max(
                0,
                prediction
            )

            week_predictions.append(
                {
                    "week":
                        future_week,

                    "sku_id":
                        sku,

                    "forecast_demand":
                        prediction
                }
            )

            # ------------------------------------------------
            # Add prediction to history
            # for next recursive week
            # ------------------------------------------------

            history_recursive = pd.concat(
                [
                    history_recursive,

                    pd.DataFrame(
                        [
                            {
                                "week":
                                    future_week,

                                "sku_id":
                                    sku,

                                "demand":
                                    prediction
                            }
                        ]
                    )
                ],
                ignore_index=True
            )

        forecast_results.extend(
            week_predictions
        )

    # ========================================================
    # CREATE FINAL FORECAST DATAFRAME
    # ========================================================

    future_forecast = pd.DataFrame(
        forecast_results
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "6-WEEK FORECAST COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        "\nForecast shape:"
    )

    print(
        future_forecast.shape
    )

    print(
        "\nNumber of weeks:",
        future_forecast[
            "week"
        ].nunique()
    )

    print(
        "Number of SKUs:",
        future_forecast[
            "sku_id"
        ].nunique()
    )

    # ========================================================
    # FORECAST STATISTICS
    # ========================================================

    print(
        "\nOverall Forecast Statistics"
    )

    print(
        "---------------------------"
    )

    print(
        future_forecast[
            "forecast_demand"
        ].describe()
    )

    # ========================================================
    # WEEKLY SUMMARY
    # ========================================================

    print(
        "\nWeekly Forecast Summary"
    )

    print(
        "-----------------------"
    )

    weekly_summary = (
        future_forecast
        .groupby("week")[
            "forecast_demand"
        ]
        .agg(
            total="sum",
            average="mean",
            minimum="min",
            maximum="max"
        )
        .reset_index()
    )

    print(
        weekly_summary
    )

    # ========================================================
    # MISSING VALUE CHECK
    # ========================================================

    print(
        "\nForecast missing values:"
    )

    print(
        future_forecast.isna().sum()
    )

    # ========================================================
    # SAVE FINAL FORECAST
    # ========================================================

    future_forecast.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nFinal forecast saved successfully!"
    )

    print(
        "File:",
        OUTPUT_FILE
    )

    print(
        "Rows:",
        len(future_forecast)
    )

    print(
        "\nDONE!"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()