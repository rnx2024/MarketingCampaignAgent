# ui_campaign_dashboard.py
import pandas as pd
import altair as alt
import streamlit as st
from services.api_client import fetch_campaigns

st.set_page_config(page_title="Campaign Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    rows = fetch_campaigns() or []
    if not rows:
        return pd.DataFrame(columns=["product","status","result_notes","created_at"])
    df = pd.DataFrame(rows)
    # normalize types
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["date"] = df["created_at"].dt.date
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    df["status"] = df["status"].fillna("pending")
    df["product"] = df["product"].fillna("unknown")
    return df.dropna(subset=["created_at"])

df = load_data()

st.title("Campaign History")

if df.empty:
    st.info("No campaigns yet.")
    st.stop()

# Filters
with st.sidebar:
    st.header("Filters")
    products = sorted(df["product"].unique())
    sel_products = st.multiselect("Product", products, default=products)
    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.date_input("Date range", value=(min_date, max_date))
    statuses = sorted(df["status"].unique())
    sel_status = st.multiselect("Status", statuses, default=statuses)

mask = (
    df["product"].isin(sel_products)
    & df["status"].isin(sel_status)
    & (df["date"] >= pd.to_datetime(date_range[0]))
    & (df["date"] <= pd.to_datetime(date_range[-1]))
)
fdf = df[mask].copy()

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total campaigns", int(fdf.shape[0]))
col2.metric("Finished", int((fdf["status"] == "finished").sum()))
col3.metric("Started", int((fdf["status"] == "started").sum()))
col4.metric("Pending", int((fdf["status"] == "pending").sum()))

# Table
st.subheader("Records")
st.dataframe(
    fdf.sort_values("created_at", ascending=False)[
        ["created_at","product","status","result_notes"]
    ],
    use_container_width=True,
    hide_index=True,
)

# Charts
st.subheader("Monthly totals")
by_month = fdf.groupby("month", as_index=False).size().rename(columns={"size":"count"})
chart1 = (
    alt.Chart(by_month)
    .mark_line(point=True)
    .encode(x="month:O", y="count:Q", tooltip=["month","count"])
    .properties(height=240)
)
st.altair_chart(chart1, use_container_width=True)

st.subheader("Status by month")
by_status = fdf.groupby(["month","status"], as_index=False).size()
chart2 = (
    alt.Chart(by_status)
    .mark_bar()
    .encode(x="month:O", y="size:Q", color="status:N", tooltip=["month","status","size"])
    .properties(height=260)
)
st.altair_chart(chart2, use_container_width=True)

st.subheader("Top products")
by_prod = fdf.groupby("product", as_index=False).size().sort_values("size", ascending=False).head(15)
chart3 = (
    alt.Chart(by_prod)
    .mark_bar()
    .encode(y=alt.Y("product:N", sort="-x"), x="size:Q", tooltip=["product","size"])
    .properties(height=28 * max(5, min(15, by_prod.shape[0])))
)
st.altair_chart(chart3, use_container_width=True)
