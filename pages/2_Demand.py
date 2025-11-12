#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Demand Page - Cake Game
Allows teams to test demand before finalizing prices.
"""

import os
import json
from datetime import date, datetime

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# =====================================
# 📅 GAME DAY SETUP
# =====================================

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-13")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()
today = date.today()
day_number = (today - start_date).days + 1

st.session_state.day = day_number
# =====================================
# 🔒 LOGIN CHECK
# =====================================

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.stop()

from datetime import date

# ❌ Specific real-world calendar dates when the game is closed
CLOSED_DATES = [
    "2025-11-22",
    "2025-11-24",
    "2025-11-26"
]

today = date.today().isoformat()

if today in CLOSED_DATES:
    st.warning(f"🚫 The game is closed today ({today}). Please come back tomorrow!")
    st.stop()


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
            📅 <span style="font-size:1.5rem;">Week {st.session_state.day}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =====================================
# 🎨 PAGE STYLING — match Leaderboard aesthetic
# =====================================

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 12px !important;
    }
    .stApp { background-color: #FFF9F3; }
    h1, h2, h3, h4, h5, h6 {
        color: #4B2E05 !important;
        text-shadow: 1px 1px 2px rgba(150,100,50,0.3);
        font-family: 'Poppins', sans-serif;
    }
    .stSubheader, .stMarkdown p {
        color: #3B2C1A !important;
        font-size: 1.8rem;
        line-height: 1.6;
    }
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
    div[data-testid="stDataFrame"] table {
        background: linear-gradient(180deg, #FFF6E8, #FCEBD6);
        border-radius: 12px;
        border-collapse: collapse;
        box-shadow: 0 3px 8px rgba(60, 40, 20, 0.15);
        color: #3B2C1A;
        font-size: 1rem;
    }
    th {
        background-color: #D6A76E !important;
        color: #fffdf9 !important;
        text-transform: uppercase;
        font-weight: 700;
        text-align: center !important;
    }
    td {
        text-align: center !important;
        padding: 8px !important;
        border-bottom: 1px solid rgba(180,140,80,0.2);
    }
    tr:hover td { background-color: #F4D6B3 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================
# 🌍 SUPABASE SETUP
# =====================================

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
# 🕒 AUTO-FILL PREVIOUS DAY PRICES IF MISSING
# =====================================

try:
    today_record = (
        supabase.table("prices")
        .select("*")
        .eq("team_name", st.session_state.team_name)
        .eq("day_number", day_number)
        .execute()
        .data
    )

    if not today_record:
        prev_record = (
            supabase.table("prices")
            .select("*")
            .eq("team_name", st.session_state.team_name)
            .lt("day_number", day_number)
            .order("day_number", desc=True)
            .limit(1)
            .execute()
            .data
        )

        if prev_record:
            last_prices = prev_record[0].get("prices_json")
            prev_day_used = prev_record[0].get("day_number")

            if prev_day_used and prev_day_used > 0:
                payload = {
                    "team_name": st.session_state.team_name,
                    "prices_json": last_prices,  # ✅ keep previous day's prices
                    "day_number": day_number,
                    "finalized": False,           # still editable
                    "auto_filled": True,          # mark as copied
                    "copied_from_day": prev_day_used,
                }
                supabase.table("prices").insert(payload).execute()
                st.info(
                    f"💡 No recent prices found — using your last submitted prices from Day {prev_day_used}."
                )
            else:
                st.warning("⚠️ No valid previous day data found to copy.")
        else:
            st.warning("⚠️ No prior prices found to carry forward.")
except Exception as e:
    st.error("❌ Failed to auto-fill previous prices.")
    st.exception(e)

# =====================================
# 🔒 CHECK IF PRICES ALREADY FINALIZED
# =====================================

existing_final = (
    supabase.table("prices")
    .select("id, finalized, auto_filled, day_number")
    .eq("team_name", st.session_state.team_name)
    .eq("day_number", day_number)
    .execute()
    .data
)

record = existing_final[0] if existing_final else {}
is_finalized = record.get("finalized", False)
is_auto_filled = record.get("auto_filled", False)
finalized_today = bool(is_finalized and not is_auto_filled)

# =====================================
# 💲 PRICING INPUTS — Unified Table Layout
# =====================================

st.subheader("📊 Set Prices per Channel and Cake")

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
    unsafe_allow_html=True,
)

disabled_inputs = finalized_today

# --- Load competitor prices (previous day)
try:
    prev_prices_data = (
        supabase.table("prices")
        .select("prices_json, day_number")
        .lt("day_number", day_number)
        .order("day_number", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if prev_prices_data:
        prev_rows = []
        for rec in prev_prices_data:
            for p in json.loads(rec["prices_json"]):
                prev_rows.append(
                    {"channel": p["channel"], "cake": p["cake"], "price_usd": p["price_usd"]}
                )
        prev_prices_df = pd.DataFrame(prev_rows)
        avg_prices = prev_prices_df.groupby(["channel", "cake"])["price_usd"].mean().to_dict()
        prev_day_used = prev_prices_data[0]["day_number"]
        st.info(f"ℹ️ Using competitor prices from Day {prev_day_used} as baseline.")
    else:
        avg_prices = {}
        st.warning("⚠️ No prior competitor prices found.")
except Exception:
    avg_prices = {}
    st.warning("⚠️ Could not load competitor prices.")

# --- Build pricing table
rows = []
for _, ch in channels_df.iterrows():
    for _, cake in cakes_df.iterrows():
        avg_price = avg_prices.get((ch["channel"], cake["name"]), 0.0)
        rows.append(
            {
                "Channel": ch["channel"],
                "Cake": cake["name"],
                "Previous day avg ($)": round(avg_price, 2),
                "Enter your price ($)": 0.0,
            }
        )

pricing_df = pd.DataFrame(rows)

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

pricing_entries = []
for _, row in edited_prices.iterrows():
    if row["Enter your price ($)"] > 0:
        pricing_entries.append(
            {
                "team_name": st.session_state.team_name,
                "channel": row["Channel"],
                "cake": row["Cake"],
                "price_usd": row["Enter your price ($)"],
                "transport_cost_usd": float(
                    channels_df.loc[
                        channels_df["channel"] == row["Channel"],
                        "transport_cost_per_unit_usd",
                    ].iloc[0]
                ),
            }
        )
# =====================================
# 📊 CALCULATE DEMAND (TEST)
# =====================================

st.subheader("📈 Test Market Demand")

if st.button("📊 Calculate Demand", disabled=disabled_inputs):
    try:
        # Load instructor parameters
        demand_params = pd.read_csv(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "data",
                "instructor_demand_competition.csv",
            )
        )

        yesterday = max(1, day_number - 1)

        # Get competitor prices from the previous day
        prev_prices_data = (
            supabase.table("prices")
            .select("team_name, prices_json, day_number")
            .eq("day_number", yesterday)
            .execute()
            .data
        )

        if prev_prices_data:
            prev_rows = []
            for rec in prev_prices_data:
                for p in json.loads(rec["prices_json"]):
                    prev_rows.append(
                        {
                            "team_name": rec["team_name"],
                            "channel": p["channel"],
                            "cake": p["cake"],
                            "price_usd": p["price_usd"],
                        }
                    )
            prev_prices_df = pd.DataFrame(prev_rows)
            avg_prices = prev_prices_df.groupby("channel")["price_usd"].mean().to_dict()
        else:
            avg_prices = {}
            st.info("ℹ️ No previous-day prices found — using 0 as competitor baseline.")

        # Demand calculation
        results = []
        for entry in pricing_entries:
            cake = entry["cake"]
            channel = entry["channel"]
            my_price = entry["price_usd"]

            params = demand_params[
                (demand_params["cake_name"] == cake)
                & (demand_params["channel"] == channel)
            ]
            if params.empty:
                continue

            alpha = params["alpha"].values[0]
            beta = params["beta"].values[0]
            gamma = params["gamma_competition"].values[0]

            avg_other = avg_prices.get(channel, 0.0)
            D = max(0, alpha - beta * my_price + gamma * (avg_other - my_price))

            results.append(
                {
                    "Cake": cake,
                    "Channel": channel,
                    "Your Price ($)": my_price,
                    "Prev-Day Avg ($)": round(avg_other, 2),
                    "Expected Demand": round(D, 1),
                }
            )

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

if "confirm_submit" not in st.session_state:
    st.session_state.confirm_submit = False

if st.button("💾 Submit Final Prices", disabled=disabled_inputs):
    if not pricing_entries:
        st.warning("⚠️ Please enter prices before saving.")
        st.stop()
    st.session_state.confirm_submit = True
    st.rerun()

if st.session_state.confirm_submit:
    st.warning("⚠️ Are you sure you want to submit? This can only be done once!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, submit now"):
            try:
                payload = {
                    "team_name": st.session_state.team_name,
                    "prices_json": json.dumps(pricing_entries),  # ✅ today's entries
                    "day_number": day_number,
                    "finalized": True,
                    "auto_filled": False,
                }
                supabase.table("prices").insert(payload).execute()
                st.success("✅ Final prices saved! You can’t edit them again today.")
                st.session_state.confirm_submit = False
                st.rerun()
            except Exception as e:
                st.error("❌ Failed to save final prices.")
                st.exception(e)

    with col2:
        if st.button("❌ Cancel"):
            st.session_state.confirm_submit = False
            st.info("Submission cancelled.")

# =====================================
# 📜 HISTORY
# =====================================

st.markdown("---")
st.subheader("📜 Previous Price Submissions")

try:
    records = (
        supabase.table("prices")
        .select("*")
        .eq("team_name", st.session_state.team_name)
        .order("id", desc=True)
        .execute()
        .data
    )

    if records:
        # Filter out auto-filled entries — only show real submissions
        filtered_records = [r for r in records if not r.get("auto_filled", False)]
    
        if filtered_records:
            for r in filtered_records:
                status = "✅ Finalized" if r.get("finalized") else "🧪 Test"
                with st.expander(f"{status} — Day {r.get('day_number', '?')}"):
                    df = pd.DataFrame(json.loads(r["prices_json"]))
                    st.dataframe(df[["channel", "cake", "price_usd"]], use_container_width=True)
        else:
            st.info("No manually submitted price history yet.")
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
