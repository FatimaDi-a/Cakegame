#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 2025
Production Plan Page — Cake Shop Simulation with Channels
@author: Fatima
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date, datetime
import matplotlib.pyplot as plt
import math

# ======================================
# ⚙️ GAME DAY SETUP
# ======================================
GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-13")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()
today = date.today()

# Ensure day_number never goes below 1 before the game starts
day_number = max(1, (today - start_date).days + 1)
st.session_state.day = day_number

# ======================================
# 🔒 LOGIN CHECK
# ======================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.stop()

# ❌ Specific real-world calendar dates when the game is closed
CLOSED_DATES = [
    "2025-11-22",
    "2025-11-24",
    "2025-11-26"
]

today_str = today.isoformat()
if today_str in CLOSED_DATES:
    st.warning(f"🚫 The game is closed today ({today_str}). Please come back tomorrow!")
    st.stop()

# ======================================
# 🌍 SUPABASE CONNECTION
# ======================================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase credentials missing.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================
# 🎨 PAGE CONFIG
# ======================================
st.set_page_config(page_title="Production Plan", page_icon="🍰", layout="wide")

st.markdown(
    """
    <style>
    /* ===== Global text size ===== */
    html, body, [class*="css"] {
        font-size: 10px !important; /* default is 16px */
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

# ======================================
# 📅 GAME DAY BANNER
# ======================================
st.markdown(
    f"""
<div style="background: linear-gradient(90deg, #F5D2A4, #E0B070);
padding: 0.6rem 1rem; border-radius: 10px; text-align: center;
color: #4B2E05; font-weight: 700; font-size: 1.2rem; margin-bottom: 1.2rem;">
📅 <span style="font-size:1.3rem;">Week {day_number}</span>
</div>
""",
    unsafe_allow_html=True
)

# ======================================
# 🧁 PAGE HEADER
# ======================================
st.title("🍰 Production Plan by Channel")
st.write(f"Welcome, **{st.session_state.team_name}**!")

# ======================================
# 🧾 LOAD DATA
# ======================================
try:
    cakes_df = pd.DataFrame(supabase.table("cakes").select("*").execute().data)
    channels_df = pd.DataFrame(supabase.table("channels").select("channel").execute().data)
except Exception as e:
    st.error("❌ Failed to load cakes or channels data.")
    st.exception(e)
    st.stop()

channels = channels_df["channel"].tolist()

# ======================================
# ⏱️ CONVERT MINUTES → HOURS
# ======================================
for col in ["oven_min_per_batch", "prep_min_per_unit", "pack_min_per_unit"]:
    if col in cakes_df.columns:
        cakes_df[col] = cakes_df[col] / 60.0

# ======================================
# 🍳 LOAD RECIPES
# ======================================
def load_recipes_case_safe():
    data = supabase.table("recipes").select("*").execute().data
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = [c.lower() for c in df.columns]
    return df

recipes_df = load_recipes_case_safe()
if recipes_df.empty:
    st.error("❌ No recipes found in Supabase.")
    st.stop()

# ======================================
# 📦 LOAD INVENTORY
# ======================================
def get_inventory(team_name, category):
    data = (
        supabase.table("inventory")
        .select("resource_name, quantity")
        .eq("team_name", team_name)
        .eq("category", category)
        .execute()
        .data
    )
    return {d["resource_name"].lower(): d["quantity"] for d in data}

ingredient_stock = get_inventory(st.session_state.team_name, "ingredient")
capacity_totals = {
    k.lower(): v for k, v in get_inventory(st.session_state.team_name, "capacity").items()
}

# ======================================
# 🧁 PLAN PRODUCTION BY CHANNEL — unified table version
# ======================================

st.subheader("🧁 Plan Your Production by Channel")

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
    💡 <strong>Note:</strong> Submitting your production plan can only be done <u>once per day</u>.
    After saving, you won’t be able to modify it until tomorrow.
    </div>
    """,
    unsafe_allow_html=True
)

# ---- FIX: Only build the empty table ONCE ----
if "production_table" not in st.session_state:

    plan_rows = []
    for _, cake_row in cakes_df.iterrows():
        cake_name = cake_row["name"]
        min_units = int(cake_row["minimum_units_if_made"])

        display_name = f"{cake_name} (min {min_units})"
        row = {"Cake (min qty)": display_name}
        for ch in channels:
            row[ch] = 0
        plan_rows.append(row)

    st.session_state.production_table = pd.DataFrame(plan_rows)


st.markdown("Enter your planned production quantity for each cake and channel below:")

edited_plan = st.data_editor(
    st.session_state.production_table,
    key="prod_table_editor",   # ← FIXED: changed widget key
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    column_config={
        "Cake (min qty)": st.column_config.Column(disabled=True, width="medium"),
        **{ch: st.column_config.NumberColumn(ch, min_value=0, step=1)
           for ch in channels},
    },
)



# --- Convert wide table to long + enforce minimum batch constraints ---
plan_entries = []
violations = []
min_batch_map = {r["name"]: int(r["minimum_units_if_made"]) for _, r in cakes_df.iterrows()}

totals = {}
for _, row in edited_plan.iterrows():
    cake = row["Cake (min qty)"].split(" (min")[0].strip()
    min_required = min_batch_map[cake]
    total_qty = sum(row[ch] for ch in channels)
    totals[cake] = total_qty

    if 0 < total_qty < min_required:
        violations.append((cake, min_required))

    for ch in channels:
        if row[ch] > 0:
            plan_entries.append({"cake": cake, "channel": ch, "qty": row[ch]})

# Min batch warnings
if violations:
    for cake, min_req in violations:
        st.warning(
            f"⚠️ {cake}: total across all channels must be at least {min_req} units if produced."
        )

batch_ok = len(violations) == 0

if not batch_ok:
    st.error("❌ You cannot submit. Some cakes do not meet the minimum batch quantity.")

if not plan_entries:
    st.info("No production quantities entered yet.")
else:
    st.success("✅ Production quantities recorded. Continue with feasibility checks below.")

# Normalize plan_df to long format
plan_df = pd.DataFrame(plan_entries)
plan_df.columns = [str(c).lower() for c in plan_df.columns]

# ======================================
# ⚙️ LOAD DEMANDS & PRICES
# ======================================
def get_latest_json(table_name, team_name):
    resp = (
        supabase.table(table_name)
        .select("*")
        .eq("team_name", team_name)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    if resp.data:
        return pd.DataFrame(json.loads(resp.data[0].get(f"{table_name}_json", "[]")))
    return pd.DataFrame()

price_df = get_latest_json("prices", st.session_state.team_name)
demand_df = get_latest_json("demands", st.session_state.team_name)

if not price_df.empty:
    price_df.columns = price_df.columns.str.lower()
if not demand_df.empty:
    demand_df.columns = demand_df.columns.str.lower()

# Fallbacks if no prices/demands yet
if price_df.empty:
    price_df = pd.DataFrame(
        {
            "cake": cakes_df["name"].repeat(len(channels)).tolist(),
            "channel": channels * len(cakes_df),
            "price": [5.0] * len(cakes_df) * len(channels),
        }
    )

if demand_df.empty:
    demand_df = pd.DataFrame(
        {
            "cake": cakes_df["name"].repeat(len(channels)).tolist(),
            "channel": channels * len(cakes_df),
            "demand": [10] * len(cakes_df) * len(channels),
        }
    )

# ======================================
# 🧠 FEASIBILITY CHECKS
# ======================================
# Total units per cake across channels
if not plan_df.empty:
    cake_totals = plan_df.groupby("cake")["qty"].sum().reset_index()
else:
    cake_totals = pd.DataFrame(columns=["cake", "qty"])

# --- Capacity requirements (in hours) ---
required = {"prep": 0.0, "oven": 0.0, "package": 0.0, "oven rental": 0.0}

for _, r in cakes_df.iterrows():
    cake_name = r["name"]

    if cake_name in cake_totals["cake"].values:
        qty = float(
            cake_totals.loc[cake_totals["cake"] == cake_name, "qty"].values[0]
        )
    else:
        qty = 0.0

    # PREP
    required["prep"] += qty * float(r["prep_min_per_unit"])

    # OVEN (batch logic)
    batches = math.ceil(qty / float(r["batch_size_units"])) if r["batch_size_units"] > 0 else 0


    required["oven"] += batches * float(r["oven_min_per_batch"])

    # OVEN RENTAL = oven time
    required["oven rental"] = required["oven"]

    # PACKAGING
    required["package"] += qty * float(r["pack_min_per_unit"])

capacity_feasible = all(
    required[k] <= capacity_totals.get(k, 0.0) + 1e-9 for k in required
)

# --- Ingredient requirements ---
def compute_required_ingredients(plan_df, recipes_df):
    needs = {}
    totals = plan_df.groupby("cake")["qty"].sum().to_dict()
    for cake, qty in totals.items():
        recipe = recipes_df[recipes_df["name"].str.lower() == cake.lower()]
        if recipe.empty:
            continue
        for ing in [
            c
            for c in recipe.columns
            if c not in ["id", "cake_id", "name", "created_at"]
        ]:
            amt = qty * float(recipe.iloc[0][ing])
            needs[ing.lower()] = needs.get(ing.lower(), 0.0) + amt
    return needs

if not plan_df.empty and "cake" in plan_df.columns:
    ingredient_needs = compute_required_ingredients(plan_df, recipes_df)
else:
    ingredient_needs = {}

ingredient_feasible = all(
    ingredient_needs[i] <= ingredient_stock.get(i, 0.0) + 1e-9
    for i in ingredient_needs
)

# ======================================
# 🧾 INGREDIENT TABLE
# ======================================
st.markdown("### 🧂 Ingredient Feasibility Check")
if ingredient_needs:
    ing_table = pd.DataFrame(
        [
            {
                "Ingredient": i.title(),
                "Needed": round(ingredient_needs[i], 2),
                "Available": round(ingredient_stock.get(i, 0.0), 2),
                "OK": "✅"
                if ingredient_needs[i] <= ingredient_stock.get(i, 0.0)
                else "❌",
            }
            for i in ingredient_needs
        ]
    )
    st.dataframe(ing_table, use_container_width=True)
else:
    st.info("No ingredients needed yet. Enter production quantities above.")

# ======================================
# 💰 PROFIT CALCULATION 
# ======================================
if not plan_df.empty and "cake" in plan_df.columns:
    price_df.columns = price_df.columns.str.lower()
    demand_df.columns = demand_df.columns.str.lower()

    # Normalize price column name
    if "net_usd" in price_df.columns:
        price_df.rename(columns={"net_usd": "price"}, inplace=True)
    elif "price_usd" in price_df.columns:
        price_df.rename(columns={"price_usd": "price"}, inplace=True)

    if "price" not in price_df.columns:
        st.error(
            "❌ Missing 'price_usd' or 'net_usd' column in Supabase prices table."
        )
        st.stop()
    if "demand" not in demand_df.columns:
        st.error("❌ Missing 'demand' column in Supabase demands table.")
        st.stop()

    # --- Safe merge with optional transport_cost_usd ---
    merge_cols = ["cake", "channel", "price"]
    if "transport_cost_usd" in price_df.columns:
        merge_cols.append("transport_cost_usd")
    else:
        price_df["transport_cost_usd"] = 0.0

    merged = (
        plan_df.merge(price_df[merge_cols], on=["cake", "channel"], how="left")
        .merge(demand_df[["cake", "channel", "demand"]], on=["cake", "channel"], how="left")
    )

    # Clean up NaNs
    merged["price"] = merged["price"].astype(float).fillna(0.0)
    merged["transport_cost_usd"] = (
        merged["transport_cost_usd"].astype(float).fillna(0.0)
    )
    merged["demand"] = merged["demand"].astype(float).fillna(0.0)
    merged["qty"] = merged["qty"].astype(float).fillna(0.0)

    # Calculate sold units and revenue
    merged["sold_units"] = np.minimum(merged["qty"], merged["demand"])
    merged["revenue"] = merged["sold_units"] * merged["price"]
    merged["transport_cost_total"] = (
        merged["sold_units"] * merged["transport_cost_usd"]
    )

    # Final profit (no double-counting purchases)
    merged["profit"] = merged["revenue"] - merged["transport_cost_total"]
    profit_today = float(merged["profit"].sum())

else:
    merged = pd.DataFrame(
        columns=["cake", "channel", "qty", "sold_units", "revenue", "profit"]
    )
    profit_today = 0.0

# ======================================
# 📊 SUMMARY
# ======================================
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    "Prep Hours",
    f"{required['prep']:.2f} / {capacity_totals.get('prep', 0.0):.2f}",
)
c2.metric(
    "Oven Hours",
    f"{required['oven']:.2f} / {capacity_totals.get('oven', 0.0):.2f}",
)
c3.metric(
    "Oven Rental",
    f"{required['oven rental']:.2f} / {capacity_totals.get('oven rental', 0.0):.2f}",
)
c4.metric(
    "Pack Hours",
    f"{required['package']:.2f} / {capacity_totals.get('package', 0.0):.2f}",
)
c5.metric("Profit (Revenue)", f"${profit_today:,.2f}")

if not capacity_feasible:
    overused = [
        k for k in required if required[k] > capacity_totals.get(k, 0.0)
    ]
    st.error(
        f"❌ Capacity exceeded for: {', '.join([k.title() for k in overused])}. Please adjust your plan."
    )
elif not ingredient_feasible:
    st.error("❌ Not enough ingredients available!")
else:
    st.success("✅ Feasible production plan!")

# ======================================
# 💾 SAVE PLAN (with confirmation) — FIXED VERSION
# ======================================

if capacity_feasible and ingredient_feasible and batch_ok:

    # Init flag
    if "confirm_submit_plan" not in st.session_state:
        st.session_state.confirm_submit_plan = False

    # Save button pressed → show confirmation
    if st.button("💾 Save Production Plan"):
        if not plan_entries:
            st.warning("⚠️ Please enter your production plan before saving.")
        else:
            st.session_state.confirm_submit_plan = True
            st.rerun()

    # Confirmation UI
    if st.session_state.confirm_submit_plan:

        st.warning("⚠️ Are you sure you want to save your production plan? This can only be done once per day!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, save now"):
                try:
                    # Prevent double submission
                    existing = (
                        supabase.table("production_plans")
                        .select("id")
                        .eq("team_name", st.session_state.team_name)
                        .gte("inserted_at", f"{today_str}T00:00:00")
                        .lte("inserted_at", f"{today_str}T23:59:59")
                        .execute()
                    )

                    if existing.data:
                        st.warning("⚠️ You already submitted today's production plan. Try again tomorrow!")
                        st.session_state.confirm_submit_plan = False
                        st.rerun()

                    # Deduct ingredients
                    for ing, used_qty in ingredient_needs.items():
                        current_qty = float(ingredient_stock.get(ing, 0.0))
                        new_qty = max(current_qty - used_qty, 0.0)
                        supabase.table("inventory").update(
                            {"quantity": new_qty, "updated_at": datetime.utcnow().isoformat()}
                        ).eq("team_name", st.session_state.team_name
                        ).eq("category", "ingredient"
                        ).ilike("resource_name", f"%{ing}%"
                        ).execute()

                    # Deduct capacities
                    for cap, used in required.items():
                        current_cap = float(capacity_totals.get(cap, 0.0))
                        new_cap = max(current_cap - used, 0.0)
                        supabase.table("inventory").update(
                            {"quantity": new_cap, "updated_at": datetime.utcnow().isoformat()}
                        ).eq("team_name", st.session_state.team_name
                        ).eq("category", "capacity"
                        ).ilike("resource_name", f"%{cap}%"
                        ).execute()

                    # Save production plan
                    supabase.table("production_plans").insert({
                        "team_name": st.session_state.team_name,
                        "plan_json": json.dumps(plan_entries),
                        "profit_usd": float(profit_today),
                        "required_json": json.dumps(required),
                        "day_number": day_number,
                    }).execute()

                    # SUCCESS → Reset table + confirmation flag
                    st.session_state.confirm_submit_plan = False
                    st.session_state.pop("production_table", None)
                    st.session_state.pop("prod_table_editor", None) 
                    st.success(f"✅ Plan saved! Expected Profit: ${profit_today:,.2f}")

                    st.rerun()

                except Exception as e:
                    st.error("❌ Failed to save production plan.")
                    st.exception(e)
                    st.session_state.confirm_submit_plan = False
                    st.session_state.pop("production_table", None)
                    st.rerun()

        with col2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_submit_plan = False
                st.rerun()


# ======================================
# 📜 HISTORY
# ======================================
st.markdown("---")
st.subheader("📜 Previous Production Plans")

try:
    records = (
        supabase.table("production_plans")
        .select("*")
        .eq("team_name", st.session_state.team_name)
        .order("id", desc=True)
        .execute()
        .data
    )
    if records:
        for r in records:
            with st.expander(
                f"Plan (Expected Profit ${float(r['profit_usd']):,.2f})"
            ):
                plan_hist = pd.DataFrame(json.loads(r["plan_json"]))
                st.dataframe(plan_hist, use_container_width=True)
    else:
        st.info("No previous plans found.")
except Exception as e:
    st.error("❌ Failed to load history.")
    st.exception(e)

# ======================================
# 🚪 LOGOUT
# ======================================
if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success("You’ve been logged out.")
    st.switch_page("Login.py")
