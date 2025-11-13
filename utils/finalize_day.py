import os
import json
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# =====================================
# 🌍 SUPABASE INIT
# =====================================
def init_supabase():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

# =====================================
# 🧮 FINALIZE FUNCTION
# =====================================
def finalize_day(target_date=None):
    """Finalize actual profits for all teams — includes carry-forward for teams with no plans."""
    supabase = init_supabase()
    today = date.today()

    # --- Determine target day (yesterday if not specified) ---
    #target_day = (
    #    datetime.strptime(target_date, "%Y-%m-%d").date()
    #    if target_date else today - timedelta(days=1)
    #)
    target_day = today

    # --- Idempotency guard: skip if all teams already finalized for target_day ---
    teams_resp = supabase.table("teams").select("team_name,last_finalized_day").execute()
    teams_data = teams_resp.data or []
    if teams_data and all((t.get("last_finalized_day") == str(today)) for t in teams_data):
        print("⏭️ Already finalized today — skipping.")
    return





    GAME_START_DATE = datetime.strptime(os.getenv("GAME_START_DATE", "2025-11-04"), "%Y-%m-%d").date()
    day_number = (target_day - GAME_START_DATE).days + 1
    print(f"📅 Game Day {day_number}")

    # --- Load production plans for that day ---
    plans_resp = (
        supabase.table("production_plans")
        .select("*")
        .gte("inserted_at", f"{target_day}T00:00:00")
        .lte("inserted_at", f"{target_day}T23:59:59")
        .execute()
    )

    plans_df = pd.DataFrame(plans_resp.data or [])

    # --- Load prices for the same day_number ---
    prices_resp = (
        supabase.table("prices")
        .select("*")
        .eq("day_number", day_number)
        .execute()
    )

    if not prices_resp.data:
        print(f"⚠️ No prices found for Day {day_number}.")
        prices_df = pd.DataFrame()
    else:
        prices_df = pd.DataFrame(prices_resp.data)

    demand_params = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "..", "data", "instructor_demand_competition.csv")
    )

    # --- Load channels for transport costs ---
    ch_resp = supabase.table("channels").select("channel, transport_cost_per_unit_usd").execute()
    ch_df = pd.DataFrame(ch_resp.data)
    ch_map = dict(zip(ch_df["channel"], ch_df["transport_cost_per_unit_usd"]))

    results = []

    # --- Compute average prices per channel (market competition) ---
    all_price_rows = []
    for rec in prices_df.to_dict("records"):
        for p in json.loads(rec.get("prices_json", "[]")):
            all_price_rows.append({
                "team_name": rec["team_name"],
                "channel": p["channel"],
                "cake": p["cake"],
                "price_usd": p["price_usd"]
            })
    all_prices = pd.DataFrame(all_price_rows) if all_price_rows else pd.DataFrame(columns=["team_name", "channel", "cake", "price_usd"])
    avg_price_by_channel = all_prices.groupby("channel")["price_usd"].mean().to_dict() if not all_prices.empty else {}

    # --- Process each team that submitted a plan ---
    if not plans_df.empty:
        for team in plans_df["team_name"].unique():
            team_plans = plans_df[plans_df["team_name"] == team]
            plan_json = json.loads(team_plans.iloc[0].get("plan_json", "[]"))
            required_json = json.loads(team_plans.iloc[0].get("required_json", "{}"))

            team_price_entries = all_prices[all_prices["team_name"] == team]
            if team_price_entries.empty:
                print(f"⚠️ No prices for {team}")
                continue

            total_profit = 0.0
            total_transport_cost = 0.0
            total_resource_cost = sum(required_json.values())

            for item in plan_json:
                cake = item.get("cake")
                channel = item.get("channel")
                qty = float(item.get("qty", 0))
                my_price = float(
                    team_price_entries[
                        (team_price_entries["cake"] == cake) &
                        (team_price_entries["channel"] == channel)
                    ]["price_usd"].fillna(0).values[0]
                    if not team_price_entries.empty else 0
                )

                params = demand_params[
                    (demand_params["cake_name"] == cake) &
                    (demand_params["channel"] == channel)
                ]
                if params.empty:
                    continue

                alpha = params["alpha"].values[0]
                beta = params["beta"].values[0]
                gamma = params["gamma_competition"].values[0]
                avg_ch_price = avg_price_by_channel.get(channel, my_price)

                demand = max(0, alpha - beta * my_price + gamma * (avg_ch_price - my_price))
                sold_units = min(qty, demand)
                revenue = sold_units * my_price
                transport_cost = sold_units * ch_map.get(channel, 0.0)
                profit = revenue - transport_cost

                total_profit += profit
                total_transport_cost += transport_cost

            # --- Fetch and update team ---
            team_data = supabase.table("teams").select("money, stock_value").eq("team_name", team).execute()
            if not team_data.data:
                continue

            money = float(team_data.data[0].get("money", 0.0))
            stock_value = float(team_data.data[0].get("stock_value", 0.0))

            new_cash = money + total_profit - total_transport_cost
            new_stock = max(stock_value - total_resource_cost, 0.0)
            total_value = new_cash + new_stock

            supabase.table("teams").update({
                "money": new_cash,
                "stock_value": new_stock,
                "last_profit": total_profit,
                "last_transport_cost": total_transport_cost,
                "last_resource_cost": total_resource_cost,
                "total_value": total_value,
                "last_finalized_day": str(target_day)
            }).eq("team_name", team).execute()

            # Also update production plan record
            supabase.table("production_plans").update({
                "profit_usd": total_profit
            }).eq("team_name", team).gte("inserted_at", f"{target_day}T00:00:00").execute()

            print(f"✅ {team}: Profit ${total_profit:,.2f}, Cash ${new_cash:,.2f}, Stock ${new_stock:,.2f}")
            results.append({"team": team, "profit": total_profit, "cash": new_cash, "stock": new_stock})

    # --- Handle teams WITHOUT plans (carry forward) ---
    # --- Handle teams WITHOUT plans (carry forward and ensure consistency) ---
    all_teams_resp = supabase.table("teams").select("team_name, money, stock_value").execute()
    all_team_names = [t["team_name"] for t in all_teams_resp.data]
    finalized_teams = set(plans_df["team_name"].unique()) if not plans_df.empty else set()
    
    for team in set(all_team_names) - finalized_teams:
        team_data = next(t for t in all_teams_resp.data if t["team_name"] == team)
        money = float(team_data.get("money", 0.0))
        stock = float(team_data.get("stock_value", 0.0))
        total_value = money + stock
    
        supabase.table("teams").update({
            "money": money,                # ✅ ensure current values are re-saved
            "stock_value": stock,
            "total_value": total_value,    # ✅ recompute from above
            "last_finalized_day": str(target_day)
        }).eq("team_name", team).execute()
    


