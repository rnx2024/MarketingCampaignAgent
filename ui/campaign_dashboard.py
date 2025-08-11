# ui/campaign_dashboard.py
import pandas as pd
import altair as alt
import streamlit as st
from services.api_client import fetch_campaigns
from state import is_authenticated

@st.cache_data(ttl=60)
def _load_data() -> pd.DataFrame:
    rows = fetch_campaigns() or []
    if not rows:
        return pd.DataFrame(columns=["product", "status", "result_notes", "created_at"])
    df = pd.DataFrame(rows)
    # normalize types
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["created_at"])
    df["date"] = df["created_at"].dt.date
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    df["status"] = df["status"].fillna("pending")
    df["product"] = df["product"].fillna("unknown")
    return df

def render_campaign_dashboard() -> None:
    st.title("Campaign Dashboard")

    if not is_authenticated():
        st.info("Login to view your dashboard.")
        return

    df = _load_data()
    if df.empty:
        st.info("No campaigns yet.")
        return

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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total campaigns", int(fdf.shape[0]))
    c2.metric("Finished", int((fdf["status"] == "finished").sum()))
    c3.metric("Started", int((fdf["status"] == "started").sum()))
    c4.metric("Pending", int((fdf["status"] == "pending").sum()))

    # Table
    st.subheader("Records")
    st.dataframe(
        fdf.sort_values("created_at", ascending=False)[
            ["created_at", "product", "status", "result_notes"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    # Charts
    st.subheader("Monthly totals")
    by_month = fdf.groupby("month", as_index=False).size().rename(columns={"size": "count"})
    st.altair_chart(
        alt.Chart(by_month)
        .mark_line(point=True)
        .encode(x="month:O", y="count:Q", tooltip=["month", "count"])
        .properties(height=240),
        use_container_width=True,
    )

    st.subheader("Status by month")
    by_status = fdf.groupby(["month", "status"], as_index=False).size()
    st.altair_chart(
        alt.Chart(by_status)
        .mark_bar()
        .encode(x="month:O", y="size:Q", color="status:N", tooltip=["month", "status", "size"])
        .properties(height=260),
        use_container_width=True,
    )

    st.subheader("Top products")
    by_prod = (
        fdf.groupby("product", as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .head(15)
    )
    st.altair_chart(
        alt.Chart(by_prod)
        .mark_bar()
        .encode(y=alt.Y("product:N", sort="-x"), x="size:Q", tooltip=["product", "size"])
        .properties(height=28 * max(5, min(15, by_prod.shape[0]))),
        use_container_width=True,
    )
