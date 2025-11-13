#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leaderboard Page - Cake Business Simulation
Now showing only Total Business Value (Cash + Stock)
"""

import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from datetime import date, datetime
from utils.finalize_day import finalize_day
import pytz

# =====================================
# 📅 GAME DAY CALCULATION
# =====================================
GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-13")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()
today = date.today()

# Ensure day_number never goes below 1 before the game starts
day_number = max(1, (today - start_date).days + 1)
st.session_state.day = day_number


# =====================================
# 🔒 LOGIN CHECK
# =====================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.switch_page("Login.py")
    st.stop()
    
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

# =====================================
# 🌍 SUPABASE SETUP
# =====================================
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing Supabase credentials. Check .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# Developer toggle: Turn off auto-finalize for testing
TEST_MODE = True

# =====================================
# 🕛 AUTO FINALIZATION
# =====================================
def auto_finalize_once_per_day():
    """Run finalize_day() once per calendar day when leaderboard is first opened."""
    today_str = str(date.today())
    if st.session_state.get("last_finalized_day") != today_str:
        try:
            msg = finalize_day()
            st.session_state["last_finalized_day"] = today_str
        except Exception as e:
            st.error("❌ Auto-finalization failed.")
            st.exception(e)

if not TEST_MODE:
    auto_finalize_once_per_day()


# =====================================
# 🎨 PAGE STYLING
# =====================================
st.set_page_config(page_title="🏆 Leaderboard", page_icon="🥇", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 10px !important;
    }
    .stApp {
        background-color: #FFF9F3;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #4B2E05 !important;
        text-shadow: 1px 1px 2px rgba(150,100,50,0.3);
        font-family: 'Poppins', sans-serif;
    }
    hr {
        border: none;
        border-top: 1px solid rgba(120,80,40,0.25);
        margin: 1.5rem 0;
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
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================
# 🏆 HEADER
# =====================================
st.title("🏆 Cake Business Leaderboard")
st.write(f"Welcome, **{st.session_state.team_name}** 👋")

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
        unsafe_allow_html=True
    )


# =====================================
# 💰 LOAD & DISPLAY DATA
# =====================================
try:
    response = supabase.table("teams").select("team_name, money, stock_value, total_value").execute()
    teams = pd.DataFrame(response.data)

    if teams.empty:
        st.info("No team data found yet.")
    else:
        # Sort by total value
        teams = teams.sort_values(by="total_value", ascending=False).reset_index(drop=True)

        # Rank + medals
        medals = ["🥇", "🥈", "🥉"]
        teams.insert(0, "Rank", [medals[i] if i < 3 else str(i + 1) for i in range(len(teams))])

        # Format currency
        teams["total_value"] = teams["total_value"].map(lambda x: f"${x:,.2f}")

        # Rename columns
        teams.rename(columns={
            "team_name": "Team",
            "total_value": "Total Value 💰"
        }, inplace=True)

        # Stylish table
        styled = (
            teams[["Rank", "Team", "Total Value 💰"]]
            .style.set_table_styles([
                {"selector": "th", "props": [
                    ("font-size", "1.1rem"),
                    ("background-color", "#D6A76E"),
                    ("color", "#fff"),
                    ("text-align", "center"),
                    ("font-weight", "700")
                ]},
                {"selector": "td", "props": [
                    ("text-align", "center"),
                    ("font-size", "1.1rem"),
                    ("color", "#3B2C1A"),
                    ("background-color", "#FFF9F3")
                ]},
                {"selector": "tr:nth-child(even) td", "props": [
                    ("background-color", "#FFF2E0")
                ]}
            ])
        )

        st.dataframe(styled, use_container_width=True, height=500)

except Exception as e:
    st.error("❌ Failed to load leaderboard data.")
    st.exception(e)



# =====================================
# 🧪 MANUAL FINALIZATION (TEST ONLY)
# =====================================

st.markdown("---")
st.subheader("🧪 Manual Finalization (Testing Only)")


if st.button("🔧 Run Finalize Day Now"):
    try:
        msg = finalize_day()
        st.success("✅ Manual finalization completed successfully!")
        st.write(msg)

        # Update session state so auto-finalize won't run again today
        st.session_state["last_finalized_day"] = str(date.today())

        st.rerun()

    except Exception as e:
        st.error("❌ Manual finalization failed.")
        st.exception(e)

# =====================================
# 🚪 LOGOUT
# =====================================
st.divider()
if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success("You’ve been logged out.")
    st.switch_page("Login.py")
