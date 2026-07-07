import os
import yaml
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# ==================================================
# PostgreSQL Connection
# ==================================================

DB_USER = "postgres"
DB_PASSWORD = "pwd"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "stock_market_db5"

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("Connected to PostgreSQL Successfully")

# ==================================================
# Main Dataset Folder
# ==================================================

root_folder = r"C:\Users\ragur\OneDrive\Documents\G_project2"

# ==================================================
# Output Folder
# ==================================================

output_folder = "Ticker_CSV"
os.makedirs(output_folder, exist_ok=True)

# ==================================================
# Read YAML Files
# ==================================================

all_records = []

for month_folder in os.listdir(root_folder):

    month_path = os.path.join(root_folder, month_folder)

    if not os.path.isdir(month_path):
        continue

    print(f"Reading Folder : {month_folder}")

    for yaml_file in os.listdir(month_path):

        if yaml_file.endswith(".yaml"):

            file_path = os.path.join(month_path, yaml_file)

            with open(file_path, "r", encoding="utf-8") as file:

                data = yaml.safe_load(file)

                if data is None:
                    continue

                if isinstance(data, list):
                    all_records.extend(data)

# ==================================================
# Convert to DataFrame
# ==================================================

df = pd.DataFrame(all_records)

if df.empty:
    print("No data found.")
    st.stop()

# ==================================================
# Data Cleaning
# ==================================================

df.drop_duplicates(inplace=True)

df.columns = df.columns.str.strip()

df["date"] = pd.to_datetime(df["date"])

df.sort_values(
    ["Ticker", "date"],
    inplace=True
)

df.reset_index(
    drop=True,
    inplace=True
)

print(df.info())
print(df.isnull().sum())
print(df.head())
print(df.columns.tolist())

# ==================================================
# Store Data in PostgreSQL
# ==================================================

df.to_sql(
    "stock_data5",
    engine,
    if_exists="replace",
    index=False
)

print("Stock data stored successfully.")

# ==================================================
# Read Data From PostgreSQL
# ==================================================

df = pd.read_sql(
    """
    SELECT *
    FROM stock_data5
    """,
    engine
)

print("Data Loaded From PostgreSQL")

print(df.head())
print(df.info())

# ==================================================
# Create Ticker-wise CSV Files (Optional)
# ==================================================

for ticker, group in df.groupby("Ticker"):

    output_file = os.path.join(
        output_folder,
        f"{ticker}.csv"
    )

    group.to_csv(
        output_file,
        index=False
    )

print("Ticker-wise CSV files created successfully.")

# ==================================================
# Yearly Return Calculation
# ==================================================

yearly_return = (
    df.groupby("Ticker", group_keys=False)
      .apply(
          lambda x: (
              (x.iloc[-1]["close"] - x.iloc[0]["close"])
              / x.iloc[0]["close"]
          ) * 100
      )
      .reset_index(name="Yearly_Return")
)

yearly_return.to_sql(
    "yearly_return",
    engine,
    if_exists="replace",
    index=False
)

# ==================================================
# Top 10 Green Stocks
# ==================================================

top10_green = (
    yearly_return.sort_values(
        by="Yearly_Return",
        ascending=False
    )
    .head(10)
)

top10_green.to_sql(
    "top10_green",
    engine,
    if_exists="replace",
    index=False
)

# ==================================================
# Top 10 Loss Stocks
# ==================================================

top10_loss = (
    yearly_return.sort_values(
        by="Yearly_Return",
        ascending=True
    )
    .head(10)
)

top10_loss.to_sql(
    "top10_loss",
    engine,
    if_exists="replace",
    index=False
)

print("Top 10 Green and Loss Stocks saved successfully.")

# =====================================================
# Market Summary
# =====================================================

green = (yearly_return["Yearly_Return"] > 0).sum()

red = (yearly_return["Yearly_Return"] < 0).sum()

average_price = df["close"].mean()

average_volume = df["volume"].mean()

summary = pd.DataFrame({
    "Metric": [
        "Green Stocks",
        "Red Stocks",
        "Average Price",
        "Average Volume"
    ],
    "Value": [
        green,
        red,
        average_price,
        average_volume
    ]
})

# Save Market Summary into PostgreSQL
summary.to_sql(
    "market_summary",
    engine,
    if_exists="replace",
    index=False
)

print(summary)

# =====================================================
# Daily Return
# =====================================================

df["Daily_Return"] = (
    df.groupby("Ticker")["close"]
      .pct_change()
)

# Save Updated Stock Data with Daily Return
df.to_sql(
    "stock_data5",
    engine,
    if_exists="replace",
    index=False
)

# =====================================================
# Volatility Calculation
# =====================================================

volatility = (
    df.groupby("Ticker")["Daily_Return"]
      .std()
      .reset_index(name="Volatility")
)

# Save Volatility Table
volatility.to_sql(
    "volatility",
    engine,
    if_exists="replace",
    index=False
)

# =====================================================
# Top 10 Most Volatile Stocks
# =====================================================

top10_volatility = (
    volatility.sort_values(
        by="Volatility",
        ascending=False
    )
    .head(10)
)

# Save Top 10 Volatile Stocks
top10_volatility.to_sql(
    "top10_volatility",
    engine,
    if_exists="replace",
    index=False
)

print("Volatility Analysis Completed.")

# =====================================================
# Streamlit Dashboard
# =====================================================

st.set_page_config(
    page_title="Nifty 50 Dashboard",
    layout="wide"
)

st.title("📈 Nifty 50 Stock Performance Dashboard")

# =====================================================
# Market Summary
# =====================================================

st.subheader("Market Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Green Stocks",
    green
)

col2.metric(
    "Red Stocks",
    red
)

col3.metric(
    "Average Price",
    f"{average_price:.2f}"
)

col4.metric(
    "Average Volume",
    f"{average_volume:.2f}"
)

# =====================================================
# Top 10 Green Stocks
# =====================================================

st.subheader("Top 10 Green Stocks")

st.dataframe(
    top10_green,
    use_container_width=True
)

# =====================================================
# Top 10 Loss Stocks
# =====================================================

st.subheader("Top 10 Loss Stocks")

st.dataframe(
    top10_loss,
    use_container_width=True
)

# =====================================================
# Top 10 Volatility Table
# =====================================================

st.subheader("Top 10 Most Volatile Stocks")

st.dataframe(
    top10_volatility,
    use_container_width=True
)

# =====================================================
# Volatility Bar Chart
# =====================================================

fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(
    top10_volatility["Ticker"],
    top10_volatility["Volatility"]
)

ax.set_title("Top 10 Most Volatile Stocks")

ax.set_xlabel("Ticker")

ax.set_ylabel("Volatility")

plt.xticks(rotation=45)

plt.tight_layout()

st.pyplot(fig)

print("Market Summary saved to PostgreSQL.")
print("Volatility saved to PostgreSQL.")
print("Top 10 Volatility saved to PostgreSQL.")
print("Streamlit Dashboard Loaded Successfully.")
# =====================================================
# Save Analysis Results to PostgreSQL
# =====================================================

# Save Top 10 Green Stocks
top10_green.to_sql(
    "top10_green",
    engine,
    if_exists="replace",
    index=False
)

# Save Top 10 Loss Stocks
top10_loss.to_sql(
    "top10_loss",
    engine,
    if_exists="replace",
    index=False
)

# Save Volatility Table
volatility.to_sql(
    "volatility",
    engine,
    if_exists="replace",
    index=False
)

# =====================================================
# Market Summary
# =====================================================

summary = pd.DataFrame({
    "Metric": [
        "Green Stocks",
        "Red Stocks",
        "Average Price",
        "Average Volume"
    ],
    "Value": [
        green,
        red,
        average_price,
        average_volume
    ]
})

summary.to_sql(
    "market_summary",
    engine,
    if_exists="replace",
    index=False
)

print("Top10 Green, Top10 Loss, Volatility and Market Summary saved successfully.")

# =====================================================
# Daily Return
# =====================================================

df["Daily_Return"] = (
    df.groupby("Ticker")["close"]
      .pct_change()
)

# =====================================================
# Cumulative Return
# =====================================================

df["Cumulative_Return"] = (
    (1 + df["Daily_Return"])
    .groupby(df["Ticker"])
    .cumprod()
    - 1
)

# Save Complete Dataset with Daily Return & Cumulative Return
df.to_sql(
    "cumulative_return",
    engine,
    if_exists="replace",
    index=False
)

print("Cumulative Return table saved successfully.")

# =====================================================
# Top 5 Performing Stocks
# =====================================================

top5 = (
    df.groupby("Ticker")["Cumulative_Return"]
      .last()
      .sort_values(ascending=False)
      .head(5)
)

# Save Top 5 Performing Stocks
top5_df = top5.reset_index()
top5_df.columns = ["Ticker", "Cumulative_Return"]

top5_df.to_sql(
    "top5_performing_stocks",
    engine,
    if_exists="replace",
    index=False
)

print("Top 5 Performing Stocks saved successfully.")

print(top5_df)

# =====================================================
# Matplotlib Chart
# =====================================================

fig, ax = plt.subplots(figsize=(12, 6))

for ticker in top5.index:

    stock = df[df["Ticker"] == ticker]

    ax.plot(
        stock["date"],
        stock["Cumulative_Return"],
        label=ticker
    )

ax.set_title("Top 5 Performing Stocks - Cumulative Return")
ax.set_xlabel("Date")
ax.set_ylabel("Cumulative Return")
ax.legend()
ax.grid(True)

plt.tight_layout()

plt.show()

# =====================================================
# Streamlit Chart
# =====================================================

st.subheader("Top 5 Performing Stocks - Cumulative Return")

fig2, ax2 = plt.subplots(figsize=(12, 6))

for ticker in top5.index:

    stock = df[df["Ticker"] == ticker]

    ax2.plot(
        stock["date"],
        stock["Cumulative_Return"],
        label=ticker
    )

ax2.set_title("Top 5 Performing Stocks - Cumulative Return")
ax2.set_xlabel("Date")
ax2.set_ylabel("Cumulative Return")
ax2.legend()

st.pyplot(fig2)

# =====================================================
# Display Top 5 Table
# =====================================================

st.subheader("Top 5 Performing Stocks")

st.dataframe(
    top5_df,
    use_container_width=True
)

print("Cumulative Return Analysis Completed Successfully.")
print("Results stored in PostgreSQL.")

# =====================================================
# Sector-wise Performance
# =====================================================

sector_df = pd.read_csv(
    r"C:\Users\ragur\OneDrive\Documents\G_project2\Sector_data - Sheet1 (1).csv"
)

sector_df.columns = sector_df.columns.str.strip()
df.columns = df.columns.str.strip()

sector_df["Symbol"] = (
    sector_df["Symbol"]
    .astype(str)
    .str.split(":")
    .str[-1]
    .str.strip()
)

# =====================================================
# Yearly Return
# =====================================================

yearly_return = (
    df.groupby("Ticker", group_keys=False)
      .apply(
          lambda x: (
              (x.iloc[-1]["close"] - x.iloc[0]["close"])
              / x.iloc[0]["close"]
          ) * 100
      )
      .reset_index(name="Yearly_Return")
)

# =====================================================
# Merge Sector Data
# =====================================================

merged_df = pd.merge(
    yearly_return,
    sector_df[["Symbol", "sector"]],
    left_on="Ticker",
    right_on="Symbol",
    how="left"
)

merged_df.to_sql(
    "sector_stock_data",
    engine,
    if_exists="replace",
    index=False
)

# =====================================================
# Sector Performance
# =====================================================

sector_performance = (
    merged_df.groupby("sector")["Yearly_Return"]
    .mean()
    .reset_index()
    .sort_values(
        "Yearly_Return",
        ascending=False
    )
)

sector_performance.to_sql(
    "sector_performance",
    engine,
    if_exists="replace",
    index=False
)

print(sector_performance)

# =====================================================
# Sector Chart
# =====================================================

fig, ax = plt.subplots(figsize=(12,6))

ax.bar(
    sector_performance["sector"],
    sector_performance["Yearly_Return"]
)

ax.set_title("Average Yearly Return by Sector")
ax.set_xlabel("Sector")
ax.set_ylabel("Average Yearly Return (%)")

plt.xticks(rotation=45)

plt.tight_layout()

plt.show()

# =====================================================
# Streamlit
# =====================================================

st.subheader("Sector-wise Performance")

st.dataframe(
    sector_performance,
    use_container_width=True
)

fig2, ax2 = plt.subplots(figsize=(12,6))

ax2.bar(
    sector_performance["sector"],
    sector_performance["Yearly_Return"]
)

ax2.set_title("Average Yearly Return by Sector")
ax2.set_xlabel("Sector")
ax2.set_ylabel("Average Yearly Return (%)")

plt.xticks(rotation=45)

st.pyplot(fig2)

print("Sector Performance Stored Successfully")

# =====================================================
# Stock Correlation
# =====================================================

correlation_data = df.pivot_table(
    index="date",
    columns="Ticker",
    values="close"
)

correlation_matrix = correlation_data.corr()

print(correlation_matrix)

correlation_matrix.reset_index().to_sql(
    "stock_correlation",
    engine,
    if_exists="replace",
    index=False
)

print("Correlation Matrix Stored Successfully")

# =====================================================
# Correlation Heatmap
# =====================================================

fig, ax = plt.subplots(figsize=(14,12))

heatmap = ax.imshow(
    correlation_matrix,
    aspect="auto"
)

ax.set_xticks(range(len(correlation_matrix.columns)))
ax.set_xticklabels(
    correlation_matrix.columns,
    rotation=90,
    fontsize=6
)

ax.set_yticks(range(len(correlation_matrix.columns)))
ax.set_yticklabels(
    correlation_matrix.columns,
    fontsize=6
)

ax.set_title("Stock Price Correlation Heatmap")

plt.colorbar(heatmap)

plt.tight_layout()

plt.show()

# =====================================================
# Streamlit Heatmap
# =====================================================

st.subheader("Stock Price Correlation Heatmap")

fig2, ax2 = plt.subplots(figsize=(14,12))

heatmap = ax2.imshow(
    correlation_matrix,
    aspect="auto"
)

ax2.set_xticks(range(len(correlation_matrix.columns)))
ax2.set_xticklabels(
    correlation_matrix.columns,
    rotation=90,
    fontsize=6
)

ax2.set_yticks(range(len(correlation_matrix.columns)))
ax2.set_yticklabels(
    correlation_matrix.columns,
    fontsize=6
)

ax2.set_title("Stock Price Correlation Heatmap")

plt.colorbar(heatmap)

st.pyplot(fig2)

# =====================================================
# Monthly Return
# =====================================================

df["date"] = pd.to_datetime(df["date"])

df["Month"] = df["date"].dt.strftime("%B")

df = df.sort_values(
    ["Ticker","date"]
)

monthly_return = (
    df.groupby(
        ["Ticker","Month"]
    )
    .apply(
        lambda x:
        (
            (x.iloc[-1]["close"]-x.iloc[0]["close"])
            /
            x.iloc[0]["close"]
        )*100
    )
    .reset_index(name="Monthly_Return")
)

monthly_return.to_sql(
    "monthly_return",
    engine,
    if_exists="replace",
    index=False
)

print(monthly_return.head())

# =====================================================
# Monthly Dashboard
# =====================================================

st.subheader("Top 5 Gainers and Losers by Month")

months = [
    "January","February","March","April",
    "May","June","July","August",
    "September","October","November","December"
]

for month in months:

    month_df = monthly_return[
        monthly_return["Month"]==month
    ]

    if month_df.empty:
        continue

    top5 = (
        month_df.sort_values(
            "Monthly_Return",
            ascending=False
        )
        .head(5)
    )

    bottom5 = (
        month_df.sort_values(
            "Monthly_Return"
        )
        .head(5)
    )

    top5.to_sql(
        f"{month.lower()}_top5_gainers",
        engine,
        if_exists="replace",
        index=False
    )

    bottom5.to_sql(
        f"{month.lower()}_top5_losers",
        engine,
        if_exists="replace",
        index=False
    )

    st.markdown(f"## {month}")

    col1,col2 = st.columns(2)

    with col1:

        st.write("Top 5 Gainers")

        fig,ax = plt.subplots(figsize=(6,4))

        ax.bar(
            top5["Ticker"],
            top5["Monthly_Return"]
        )

        ax.set_title(f"{month} Top 5 Gainers")

        ax.set_xlabel("Ticker")

        ax.set_ylabel("Return (%)")

        plt.xticks(rotation=45)

        st.pyplot(fig)

    with col2:

        st.write("Top 5 Losers")

        fig,ax = plt.subplots(figsize=(6,4))

        ax.bar(
            bottom5["Ticker"],
            bottom5["Monthly_Return"]
        )

        ax.set_title(f"{month} Top 5 Losers")

        ax.set_xlabel("Ticker")

        ax.set_ylabel("Return (%)")

        plt.xticks(rotation=45)

        st.pyplot(fig)

print("Sector Analysis Completed Successfully.")
print("Correlation Analysis Completed Successfully.")
print("Monthly Analysis Completed Successfully.")
print("All analysis tables saved to PostgreSQL.")

        
