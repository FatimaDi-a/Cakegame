#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leaderboard Page - Cake Business Simulation
Stylish warm leaderboard with caramel-ivory theme
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
GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-04")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()

today = date.today()
day_number = (today - start_date).days + 1  # Day 1 starts on the start date


# =====================================
# 🔒 LOGIN CHECK
# =====================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.switch_page("Login.py")
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

# =====================================
# 🕛 AUTO FINALIZATION CHECK (at midnight)
# =====================================
def auto_finalize_previous_day():
    tz = pytz.timezone("Asia/Dubai")
    now = datetime.now(tz)
    today = date.today()

    # Only run once per day, between 00:00 and 00:10
    if now.hour == 0 and now.minute < 10:
        last_finalized = st.session_state.get("last_finalized_day", None)
        if last_finalized == today:
            return

        st.info("🕛 Finalizing profits for yesterday...")
        try:
            message = finalize_day()
            st.success(message)
            st.session_state["last_finalized_day"] = today
        except Exception as e:
            st.error("❌ Finalization failed.")
            st.exception(e)

auto_finalize_previous_day()

# =====================================
# 🎨 PAGE STYLING
# =====================================
st.set_page_config(page_title="🏆 Leaderboard", page_icon="🥇", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 12px !important;
    }

    .stApp {
        background-color: #FFF9F3;
    }

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

    [data-testid="stMetricValue"] {
        color: #4B2E05 !important;
    }

    div[data-testid="stExpander"] {
        background-color: rgba(255, 247, 234, 0.95);
        border-radius: 12px;
        border: 1px solid rgba(180,140,80,0.2);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    canvas {
        background-color: #FFF9F3 !important;
        border-radius: 12px;
    }

    .stButton>button[kind="secondary"] {
        background-color: #FFF2E0 !important;
        color: #4B2E05 !important;
        border: 1px solid #D6A76E !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
# 🏆 HEADER
# =====================================
st.title("🏆 Cake Business Leaderboard")
st.write(f"Welcome, **{st.session_state.team_name}** 👋")
st.write(f"Your current balance: **${st.session_state.money:,.2f}**")

st.caption(f"📅 Last updated automatically at midnight — showing profits finalized from Day {day_number-1}.")

# =====================================
# 💰 LOAD DATA
# =====================================
try:
    response = supabase.table("teams").select("team_name, money").execute()
    teams = pd.DataFrame(response.data)

    if teams.empty:
        st.info("No team data found yet.")
    else:
        # Sort by balance
        teams = teams.sort_values(by="money", ascending=False).reset_index(drop=True)

        # Add rank + medals
        medals = ["🥇", "🥈", "🥉"]
        teams.insert(0, "Rank", [medals[i] if i < 3 else str(i + 1) for i in range(len(teams))])

        # Format money
        teams["money"] = teams["money"].map(lambda x: f"${x:,.2f}")

        # Rename columns
        teams.rename(columns={"team_name": "Team", "money": "Balance"}, inplace=True)

        # === Table styling without highlight ===
        styled = (
            teams[["Rank", "Team", "Balance"]]
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


        st.dataframe(
            styled,
            use_container_width=True,
            height=450
        )

except Exception as e:
    st.error("❌ Failed to load leaderboard data.")
    st.exception(e)

# =====================================
# 🚪 LOGOUT BUTTON
# =====================================
st.divider()
if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success("You’ve been logged out.")
    st.switch_page("Login.py")
