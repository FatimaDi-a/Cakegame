#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 16:44:33 2025

@author: fatima
"""

# utils/finalize_day.py

import os
from datetime import date, datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd

# Initialize Supabase
def init_supabase():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def finalize_day(target_date=None):
    """Finalize profits for a given day (default = yesterday)."""
    supabase = init_supabase()

    # Determine which day to finalize
    today = date.today()
    if target_date:
        target_day = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target_day = today - timedelta(days=1)

    print(f"🔄 Finalizing profits for {target_day}")

    # Fetch all production plans for that day
    plans_resp = supabase.table("production_plans").select("*") \
        .gte("inserted_at", f"{target_day}T00:00:00") \
        .lte("inserted_at", f"{target_day}T23:59:59") \
        .execute()

    if not plans_resp.data:
        print("⚠️ No production plans found for that day.")
        return "No plans found."

    df = pd.DataFrame(plans_resp.data)
    df["profit_usd"] = df["profit_usd"].astype(float)

    # Group by team
    profits = df.groupby("team_name")["profit_usd"].sum().reset_index()

    # Update each team's balance
    for _, row in profits.iterrows():
        team = row["team_name"]
        profit = row["profit_usd"]

        team_resp = supabase.table("teams").select("money").eq("team_name", team).execute()
        current_money = float(team_resp.data[0]["money"]) if team_resp.data else 0.0
        new_balance = current_money + profit

        supabase.table("teams").update({"money": new_balance}).eq("team_name", team).execute()
        print(f"✅ {team}: +${profit:,.2f} → New balance ${new_balance:,.2f}")

    return f"Finalized {len(profits)} teams for {target_day}."
