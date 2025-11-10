#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin: End-of-Day Market Finalization
Computes actual demand and true profit for the day after all teams submit prices.
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
from supabase import create_client
from dotenv import load_dotenv
import numpy as np

# =====================================
# ⚙️ CONFIG
# =====================================
st.set_page_config(page_title="Admin — Finalize Market Day", page_icon="🕛", layout="wide")
st.title("🕛 End-of-Day Profit Calculation")

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Determine game day
GAME_START_DATE = datetime.strptime(os.getenv("GAME_START_DATE", "2025-11-04"), "%Y-%m-%d").date()
today = date.today()
day_number = (today - GAME_START_DATE).days + 1

st.info(f"Today is Day {day_number} — this page finalizes **profits for Day {day_number}** using today’s prices.")

# =====================================
# 🚀 FINALIZE MARKET
# =====================================
if st.button("🚀 Run Market Finalization"):
    try:
        # --- Load finalized prices for today
        prices_data = (
            supabase.table("prices")
            .select("*")
            .eq("day_number", day_number)
            .eq("finalized", True)
            .execute()
            .data
        )
        if not prices_data:
            st.warning("⚠️ No finalized prices found for today yet.")
            st.stop()

        # --- Load production plans
        plans_data = (
            supabase.table("production_plans")
            .select("*")
            .eq("day", today.isoformat())
            .execute()
            .data
        )

        # --- Load demand parameters
        demand_params = pd.read_csv(
            os.path.join(os.path.dirname(__file__), "..", "data", "instructor_demand_competition.csv")
        )

        # --- Flatten all prices into dataframe
        all_prices = []
        for rec in prices_data:
            for p in json.loads(rec["prices_json"]):
                p["team_name"] = rec["team_name"]
                all_prices.append(p)
        df_prices = pd.DataFrame(all_prices)

        # --- Average today's prices by channel
        avg_today = df_prices.groupby("channel")["price_usd"].mean().to_dict()

        # --- Prepare results list
        results = []

        # =====================================
        # 💰 TRUE PROFIT CALCULATION (NO INVENTORY)
        # =====================================
        for team in df_prices["team_name"].unique():
            st.write(f"📊 Calculating profit for **{team}**...")
            team_prices = df_prices[df_prices["team_name"] == team]
            plan_entry = next((p for p in plans_data if p["team_name"] == team), None)
            plan_list = json.loads(plan_entry["plan_json"]) if plan_entry else []
            plan_df = pd.DataFrame(plan_list)

            if plan_df.empty or "cake" not in plan_df.columns:
                results.append({"team_name": team, "profit_usd": 0.0})
                continue

            # Load price and demand dataframes for merging
            price_df = team_prices.copy()
            demand_df = demand_params.rename(columns={"cake_name": "cake"})[
                ["cake", "channel", "alpha", "beta", "gamma_competition", "sigma_noise"]
            ].copy()

            # --- Normalize column names
            price_df.columns = price_df.columns.str.lower()
            if "net_usd" in price_df.columns:
                price_df.rename(columns={"net_usd": "price"}, inplace=True)
            elif "price_usd" in price_df.columns:
                price_df.rename(columns={"price_usd": "price"}, inplace=True)

            # --- Compute demand using the demand model
            demand_records = []
            for _, row in price_df.iterrows():
                cake, ch, my_price = row["cake"], row["channel"], row["price"]
                params = demand_params[
                    (demand_params["cake_name"] == cake) & (demand_params["channel"] == ch)
                ]
                if params.empty:
                    continue

                α = params.alpha.values[0]
                β = params.beta.values[0]
                γ = params.gamma_competition.values[0]
                σ = params.sigma_noise.values[0]
                avg_ch_price = avg_today.get(ch, my_price)
                ε = np.random.normal(0, σ)
                demand = max(0, α - β * my_price + γ * (avg_ch_price - my_price) + ε)
                demand_records.append({"cake": cake, "channel": ch, "demand": demand})
            demand_df = pd.DataFrame(demand_records)

            # --- Merge plan, price, and demand data
            merged = (
                plan_df.merge(
                    price_df[["cake", "channel", "price", "transport_cost_usd"]],
                    on=["cake", "channel"],
                    how="left",
                )
                .merge(
                    demand_df[["cake", "channel", "demand"]],
                    on=["cake", "channel"],
                    how="left",
                )
            )

            # --- Clean data and compute metrics
            merged["price"] = merged["price"].astype(float).fillna(0)
            merged["transport_cost_usd"] = merged["transport_cost_usd"].astype(float).fillna(0)
            merged["demand"] = merged["demand"].astype(float).fillna(0)
            merged["qty"] = merged["qty"].astype(float).fillna(0)

            merged["sold_units"] = np.minimum(merged["qty"], merged["demand"])
            merged["revenue"] = merged["sold_units"] * merged["price"]
            merged["transport_cost_total"] = merged["sold_units"] * merged["transport_cost_usd"]
            merged["profit"] = merged["revenue"] - merged["transport_cost_total"]

            # ✅ Final profit (no inventory adjustment)
            profit_today = merged["profit"].sum()
            results.append({"team_name": team, "profit_usd": profit_today})

        # =====================================
        # 🧾 UPDATE SUPABASE
        # =====================================
        for r in results:
            team_data = (
                supabase.table("teams")
                .select("money")
                .eq("team_name", r["team_name"])
                .execute()
                .data
            )
            if not team_data:
                continue
            current_money = team_data[0]["money"] or 0.0
            new_balance = current_money + r["profit_usd"]

            # Update team balance and daily profit
            supabase.table("teams").update({"money": new_balance}).eq(
                "team_name", r["team_name"]
            ).execute()
            supabase.table("production_plans").update({"profit_usd": r["profit_usd"]}).eq(
                "team_name", r["team_name"]
            ).eq("day", today.isoformat()).execute()

        # =====================================
        # ✅ DISPLAY RESULTS
        # =====================================
        st.success("✅ Market finalized and profits updated successfully!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)

    except Exception as e:
        st.error("❌ Failed to finalize market.")
        st.exception(e)
