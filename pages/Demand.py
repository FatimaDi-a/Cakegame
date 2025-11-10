#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Demand Page - Cake Game
Allows teams to test demand before finalizing prices.
"""

import streamlit as st
import pandas as pd
import json
import os
import numpy as np
from supabase import create_client
from dotenv import load_dotenv
from datetime import date, datetime
# =====================================
# 📅 GAME DAY SETUP
# =====================================
GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-04")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()
today = date.today()
day_number = (today - start_date).days + 1
st.session_state.day = day_number

st.set_page_config(page_title="Demand", page_icon="📈", layout="wide")
if "day" in st.session_state:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #F5D2A4, #E0B070);
            padding: 0.6rem 1rem;
            border-radius: 10px;
            text-align: center;
            color: #4B2E05;
            font-weight: 700;
            font-size: 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        ">
            📅 <span style="font-size:1.5rem;">Day {st.session_state.day}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
# =====================================
# 🎨 PAGE STYLING — match Leaderboard aesthetic
# =====================================
st.markdown(
    """

    <style>
    /* ===== Global text size ===== */
    html, body, [class*="css"] {
        font-size: 12px !important; /* default is 16px */
    }
    /* ===== Background ===== */
    .stApp {
        background-color: #FFF9F3;
    }

    /* ===== Headings ===== */
    h1, h2, h3, h4, h5, h6 {
        color: #4B2E05 !important;
        text-shadow: 1px 1px 2px rgba(150,100,50,0.3);
        font-family: 'Poppins', sans-serif;
    }

    /* ===== Subheaders ===== */
    .stSubheader, .stMarkdown p {
    color: #3B2C1A !important;
    font-size: 1.8rem; 
    line-height: 1.6;
}


    /* ===== Divider lines ===== */
    hr {
        border: none;
        border-top: 1px solid rgba(120,80,40,0.25);
        margin: 1.5rem 0;
    }

    /* ===== Buttons ===== */
    .stButton>button {
        background-color: #F5D2A4 !important;
        color: #4B2E05 !important;
        border: 1px solid #C68E53 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.25);
        transition: all 0.2s ease-in-out;
    }

    .stButton>button:hover {
        background-color: #E0B070 !important;
        transform: scale(1.05);
    }

    /* ===== Metric cards ===== */
    [data-testid="stMetricValue"] {
        color: #4B2E05 !important;
    }

    /* ===== Expander styling ===== */
    div[data-testid="stExpander"] {
        background-color: rgba(255, 247, 234, 0.95);
        border-radius: 12px;
        border: 1px solid rgba(180,140,80,0.2);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* ===== Data tables ===== */
    div[data-testid="stDataFrame"] table {
        background: linear-gradient(180deg, #FFF6E8, #FCEBD6);
        border-radius: 12px;
        border-collapse: collapse;
        overflow: hidden;
        box-shadow: 0px 3px 8px rgba(60, 40, 20, 0.15);
        color: #3B2C1A;
        font-size: 1rem;
    }

    th {
        background-color: #D6A76E !important;
        color: #fffdf9 !important;
        text-transform: uppercase;
        font-weight: 700;
        text-align: center !important;
        padding: 10px 8px !important;
    }

    td {
        text-align: center !important;
        padding: 8px !important;
        border-bottom: 1px solid rgba(180,140,80,0.2);
    }

    tr:nth-child(even) td {
        background-color: rgba(255, 248, 230, 0.85) !important;
    }

    tr:nth-child(odd) td {
        background-color: rgba(255, 242, 220, 0.95) !important;
    }

    tr:hover td {
        background-color: #F4D6B3 !important;
        transition: all 0.2s ease-in-out;
    }

    /* ===== Pie chart background ===== */
    canvas {
        background-color: #FFF9F3 !important;
        border-radius: 12px;
    }

    /* ===== Logout Button ===== */
    .stButton>button[kind="secondary"] {
        background-color: #FFF2E0 !important;
        color: #4B2E05 !important;
        border: 1px solid #D6A76E !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================
# 🔒 LOGIN CHECK
# =====================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.stop()

# =====================================
# 🌍 SUPABASE SETUP
# =====================================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase credentials missing.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================
# 🎨 PAGE SETUP
# =====================================

st.title("📈 Market Demand")
st.write(f"Welcome, **{st.session_state.team_name}**!")
st.write(f"Current Balance: **${st.session_state.money:,.2f}**")

# =====================================
# 🧾 LOAD DATA
# =====================================
try:
    cakes_df = pd.DataFrame(supabase.table("cakes").select("name").execute().data)
    channels_df = pd.DataFrame(supabase.table("channels").select("*").execute().data)
except Exception:
    local_path = os.path.join(os.path.dirname(__file__), "..", "data", "channels.csv")
    if os.path.exists(local_path):
        channels_df = pd.read_csv(local_path)
    else:
        st.error("❌ Could not load channels.")
        st.stop()

if cakes_df.empty or channels_df.empty:
    st.error("❌ Missing data: please ensure cakes and channels exist.")
    st.stop()

# =====================================
# 🔒 CHECK IF PRICES ALREADY FINALIZED
# =====================================
existing_final = supabase.table("prices") \
    .select("id, finalized, day_number") \
    .eq("team_name", st.session_state.team_name) \
    .eq("day_number", day_number) \
    .execute().data

finalized_today = bool(existing_final and existing_final[0].get("finalized", False))



# =====================================
# 💲 PRICING INPUTS — Unified Table Layout (with note)
# =====================================
st.subheader("📊 Set Prices per Channel and Cake")

# ⚠️ One-time submission reminder
st.markdown(
    """
    <div style="
        background-color: #FFF2E0;
        border: 1px solid #E0B070;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 1rem;
        color: #4B2E05;
        font-weight: 600;
        font-size: 1.05rem;
    ">
    💡 <strong>Note:</strong> Submitting prices can only be done <u>once per day</u>. 
    After you click <em>Submit Final Prices</em>, you won't be able to edit them again for today.
    </div>
    """,
    unsafe_allow_html=True
)

disabled_inputs = finalized_today

# --- Get yesterday’s average competitor prices ---
yesterday = max(1, day_number - 1)
try:
    prev_prices_data = (
        supabase.table("prices")
        .select("prices_json, day_number")
        .eq("day_number", yesterday)
        .execute()
        .data
    )

    if prev_prices_data:
        prev_rows = []
        for rec in prev_prices_data:
            for p in json.loads(rec["prices_json"]):
                prev_rows.append({
                    "channel": p["channel"],
                    "cake": p["cake"],
                    "price_usd": p["price_usd"]
                })
        prev_prices_df = pd.DataFrame(prev_rows)
        avg_prices = (
            prev_prices_df.groupby(["channel", "cake"])["price_usd"].mean().to_dict()
        )
    else:
        avg_prices = {}
        st.info("ℹ️ No previous-day prices found — using 0 as baseline.")
except Exception:
    avg_prices = {}
    st.warning("⚠️ Could not load previous-day prices.")

# --- Build full table of all (channel, cake) combinations ---
rows = []
for _, ch in channels_df.iterrows():
    for _, cake in cakes_df.iterrows():
        avg_price = avg_prices.get((ch["channel"], cake["name"]), 0.0)
        rows.append({
            "Channel": ch["channel"],
            "Cake": cake["name"],
            "Previous day avg ($)": round(avg_price, 2),
            "Enter your price ($)": 0.0
        })

pricing_df = pd.DataFrame(rows)

st.markdown("Enter your price for each channel and cake combination below:")

# --- Editable table ---
edited_prices = st.data_editor(
    pricing_df,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    disabled=disabled_inputs,
    key="price_table",
    column_config={
        "Channel": st.column_config.Column(disabled=True),
        "Cake": st.column_config.Column(disabled=True),
        "Previous day avg ($)": st.column_config.Column(disabled=True),
        "Enter your price ($)": st.column_config.NumberColumn(
            "Enter your price ($)", min_value=0.0, step=0.1
        ),
    },
)

# --- Build pricing_entries for saving later ---
pricing_entries = []
for _, row in edited_prices.iterrows():
    if row["Enter your price ($)"] > 0:
        pricing_entries.append({
            "team_name": st.session_state.team_name,
            "channel": row["Channel"],
            "cake": row["Cake"],
            "price_usd": row["Enter your price ($)"],
            "transport_cost_usd": float(
                channels_df.loc[channels_df["channel"] == row["Channel"], "transport_cost_per_unit_usd"].iloc[0]
            ),
        })


# =====================================
# 📊 CALCULATE DEMAND (TEST)
# =====================================
st.subheader("📈 Test Market Demand")

if st.button("📊 Calculate Demand", disabled=disabled_inputs):
    try:
        demand_params = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "instructor_demand_competition.csv"))
        yesterday = max(1, day_number - 1)

        # Previous day's competitor prices
        prev_prices_data = supabase.table("prices") \
            .select("team_name, prices_json, day_number") \
            .eq("day_number", yesterday) \
            .execute().data

        if prev_prices_data:
            prev_rows = []
            for rec in prev_prices_data:
                for p in json.loads(rec["prices_json"]):
                    prev_rows.append({
                        "team_name": rec["team_name"],
                        "channel": p["channel"],
                        "cake": p["cake"],
                        "price_usd": p["price_usd"]
                    })
            prev_prices_df = pd.DataFrame(prev_rows)
            avg_prices = prev_prices_df.groupby("channel")["price_usd"].mean().to_dict()
        else:
            avg_prices = {}
            st.info("ℹ️ No previous-day prices found — using 0 as competitor baseline.")

        # Demand calculation
        results = []
        for entry in pricing_entries:
            cake, channel, my_price = entry["cake"], entry["channel"], entry["price_usd"]

            params = demand_params[
                (demand_params["cake_name"] == cake) & (demand_params["channel"] == channel)
            ]
            if params.empty:
                continue

            α = params["alpha"].values[0]
            β = params["beta"].values[0]
            γ = params["gamma_competition"].values[0]
            σ = params["sigma_noise"].values[0]
            avg_other = avg_prices.get(channel, 0.0)
            ε = np.random.normal(0, σ)
            D = max(0, α - β * my_price + γ * (avg_other - my_price) + ε)

            results.append({
                "Cake": cake,
                "Channel": channel,
                "Your Price ($)": my_price,
                "Prev-Day Avg ($)": round(avg_other, 2),
                "Expected Demand": round(D, 1)
            })

        if results:
            st.success("✅ Demand calculated successfully!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚠️ No matching demand parameters found.")

    except Exception as e:
        st.error("❌ Failed to calculate demand.")
        st.exception(e)

# =====================================
# 💾 SAVE FINAL PRICES (LOCK-IN)
# =====================================
if st.button("💾 Submit Final Prices", disabled=disabled_inputs):
    if not pricing_entries:
        st.warning("⚠️ Please enter prices before saving.")
        st.stop()

    try:
        payload = {
            "team_name": st.session_state.team_name,
            "prices_json": json.dumps(pricing_entries),
            "day_number": day_number,
            "finalized": True
        }
        supabase.table("prices").insert(payload).execute()
        st.success("✅ Final prices saved! You can’t edit them again today.")
        st.rerun()
    except Exception as e:
        st.error("❌ Failed to save final prices.")
        st.exception(e)
# =====================================
# 📈 MARKET PRICE HISTORY VISUALIZATION
# =====================================
st.markdown("---")
st.subheader("📊 Market Price Trends (Previous Days)")

try:
    # Get all past price data (before today)
    history_data = supabase.table("prices") \
        .select("day_number, prices_json") \
        .lt("day_number", day_number) \
        .execute().data

    if history_data:
        all_rows = []
        for rec in history_data:
            for p in json.loads(rec["prices_json"]):
                all_rows.append({
                    "day_number": rec["day_number"],
                    "channel": p["channel"],
                    "cake": p["cake"],
                    "price_usd": p["price_usd"]
                })

        df_hist = pd.DataFrame(all_rows)

        # Optional: Let player filter by channel
        channels = sorted(df_hist["channel"].unique())
        selected_channel = st.selectbox("Filter by Channel", ["All"] + channels)

        if selected_channel != "All":
            df_hist = df_hist[df_hist["channel"] == selected_channel]

        avg_prices = (
            df_hist.groupby(["day_number", "cake"])["price_usd"]
            .mean()
            .reset_index()
        )


        avg_price_table = (
        df_hist.groupby(["day_number", "channel", "cake"])["price_usd"]
        .mean()
        .reset_index()
        .rename(columns={"price_usd": "Average Price ($)"})
    )
    
        st.dataframe(avg_price_table, use_container_width=True)



    else:
        st.info("ℹ️ No historical price data yet — charts will appear once previous days exist.")

except Exception as e:
    st.error("❌ Failed to load market price history.")
    st.exception(e)

# =====================================
# 📜 HISTORY
# =====================================
st.markdown("---")
st.subheader("📜 Previous Price Submissions")

try:
    records = supabase.table("prices") \
        .select("*") \
        .eq("team_name", st.session_state.team_name) \
        .order("id", desc=True) \
        .execute().data
    if records:
        for r in records:
            status = "✅ Finalized" if r.get("finalized") else "🧪 Test"
            with st.expander(f"{status} — Day {r.get('day_number', '?')}"):
                df = pd.DataFrame(json.loads(r["prices_json"]))
                st.dataframe(df[["channel", "cake", "price_usd"]], use_container_width=True)
    else:
        st.info("No prior price submissions yet.")
except Exception as e:
    st.error("❌ Could not load price history.")
    st.exception(e)

# =====================================
# 🚪 LOGOUT
# =====================================
if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success("You’ve been logged out.")
    st.switch_page("Login.py")
