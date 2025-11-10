#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 23 14:47:57 2025

@author: fatima
"""
import streamlit as st
import pandas as pd
import json
import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from datetime import date, datetime

GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-04")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()

today = date.today()
day_number = (today - start_date).days + 1  # Day 1 starts on the start date

# Save in session state
st.session_state.day = day_number

# ============================
# 🔒 LOGIN CHECK
# ============================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")
    st.stop()

# ============================
# 🌍 SUPABASE SETUP
# ============================
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase credentials missing. Check your .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================
# 🧁 PAGE HEADER
# ============================
st.set_page_config(page_title="Investments", page_icon="💰", layout="wide")
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
# 📅 GAME DAY BANNER
# =====================================
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
            font-size: 1.2rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        ">
            📅 <span style="font-size:1.3rem;">Day {st.session_state.day}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


st.title("💰 Investment Decisions")
st.write(f"Welcome, **{st.session_state.team_name}**!")
st.write(f"Current Balance: **${st.session_state.money:,.2f}**")



# ============================
# 📊 LOAD CSV DATA
# ============================
try:
    data_dir = Path(__file__).parent.parent / "data"

    ingredients = pd.read_csv(data_dir / "ingredients.csv")
    wages = pd.read_csv(data_dir / "wages_energy.csv")
except FileNotFoundError:
    st.error("❌ Missing required CSV files (ingredients.csv or wages_energy.csv).")
    st.stop()


# ============================
# 🧺 INGREDIENTS SECTION (Unified Editable Table)
# ============================
st.subheader("🧺 Ingredients Purchase")

# Fetch current stock from inventory (if available)
inventory_data = (
    supabase.table("inventory")
    .select("resource_name, quantity")
    .eq("team_name", st.session_state.team_name)
    .eq("category", "ingredient")
    .execute()
)
current_stock = {item["resource_name"]: item["quantity"] for item in inventory_data.data} if inventory_data.data else {}

# Build base DataFrame
ingredients_df = ingredients.copy()
ingredients_df["Current stock"] = ingredients_df["ingredient"].map(current_stock).fillna(0)
ingredients_df["Unit cost (unit)"] = ingredients_df.apply(
    lambda x: f"${x['unit_cost_usd']:.2f} ({x['unit']})", axis=1
)
ingredients_df["Enter value"] = 0.0  # editable column

# Reorder and rename for display
ingredients_display = ingredients_df[["ingredient", "Unit cost (unit)", "Current stock", "Enter value"]]
ingredients_display = ingredients_display.rename(columns={"ingredient": "Ingredient"})

st.markdown("Enter the quantities you want to buy below:")

# Editable table
edited_df = st.data_editor(
    ingredients_display,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="ingredients_table",
    column_config={
        "Ingredient": st.column_config.Column(disabled=True),
        "Unit cost (unit)": st.column_config.Column(disabled=True),
        "Current stock": st.column_config.Column(disabled=True),
        "Enter value": st.column_config.NumberColumn("Enter value", min_value=0.0, step=0.5),
    }
)

# Calculate total
merged = ingredients.merge(edited_df, left_on="ingredient", right_on="Ingredient")
merged["subtotal_usd"] = merged["Enter value"] * merged["unit_cost_usd"]
total_ingredients_cost = merged["subtotal_usd"].sum()

# Prepare entries for saving
ingredient_entries = [
    {
        "ingredient": row["ingredient"],
        "unit": row["unit"],
        "unit_cost_usd": float(row["unit_cost_usd"]),
        "buy_qty": float(row["Enter value"]),
        "subtotal_usd": float(row["subtotal_usd"])
    }
    for _, row in merged.iterrows()
    if row["Enter value"] > 0
]

st.markdown(f"**Total Ingredients Cost:** ${total_ingredients_cost:,.2f}")


# ============================
# 🏭 PRODUCTION CAPACITY (Prep, Oven, Package Only)
# ============================
st.subheader("🏭 Production Capacity")

capacity_entries = []
total_capacity_cost = 0.0

# Filter for only the 3 relevant rows
valid_params = [
    "prep_wage_usd_per_hour",
    "oven_wage_usd_per_hour",
    "package_wage_usd_per_hour"
]

filtered_wages = wages[wages["parameter"].isin(valid_params)]

header_cols = st.columns([3, 2, 2])
header_cols[0].markdown("**Capacity Type**")
header_cols[1].markdown("**Rate (USD/hr)**")
header_cols[2].markdown("**Hours to Buy**")

for idx, row in filtered_wages.iterrows():
    param = row["parameter"]
    rate = float(row["value"])

    # Display friendly label
    label = (
    param.replace("_wage_usd_per_hour", "")
         .replace("_usd_per_hour", "")
         .replace("_wage", "")
         .replace("_", " ")
         .title()
)


    c1, c2, c3 = st.columns([3, 2, 2])
    c1.write(label)
    c2.write(f"${rate:.2f}/hr")
    hours = c3.number_input(
        f"Hours for {label}",
        min_value=0.0,
        step=0.5,
        key=f"cap_{idx}"
    )
    subtotal = rate * hours
    total_capacity_cost += subtotal

    capacity_entries.append({
        "parameter": param,          # keep internal name for DB consistency
        "display_name": label,       # keep pretty version for UI
        "unit_cost_usd": rate,
        "hours": hours,
        "subtotal_usd": subtotal
    })

st.markdown(f"**Total Capacity Cost:** ${total_capacity_cost:,.2f}")

# ============================
# 📈 SUMMARY
# ============================
st.markdown("---")
# Get latest balance from Supabase
team_data = supabase.table("teams").select("money").eq("team_name", st.session_state.team_name).execute()
if team_data.data:
    current_balance = team_data.data[0]["money"]
    st.session_state.money = current_balance
else:
    current_balance = st.session_state.money  # fallback

total_investment = total_ingredients_cost + total_capacity_cost
remaining = current_balance - total_investment

col1, col2, col3 = st.columns(3)
col1.metric("Current Balance", f"${current_balance:,.2f}")
col2.metric("Total Investment", f"${total_investment:,.2f}")
col3.metric("Remaining After Purchase", f"${remaining:,.2f}")


# ============================
# 💾 SAVE TO SUPABASE
# ============================
if total_investment > current_balance:
    st.error("⚠️ You exceeded your budget! Please adjust your quantities.")
else:
    if st.button("💾 Save Investment"):
        today = date.today().isoformat()

        payload = {
            "team_name": st.session_state.team_name,
            "ingredients_json": json.dumps(ingredient_entries),
            "capacity_json": json.dumps(capacity_entries),
            "total_cost_usd": total_investment,
        }
    
        try:
            # Get total prior spending from Supabase
            prev_investments = supabase.table("investments") \
                .select("total_cost_usd") \
                .eq("team_name", st.session_state.team_name) \
                .execute()
            spent_so_far = sum(inv["total_cost_usd"] for inv in prev_investments.data)
    
            remaining_budget = current_balance
    
            if total_investment > remaining_budget:
                st.error(f"⚠️ Not enough balance! You only have ${remaining_budget:,.2f} left.")
                st.stop()
    
            # Save investment record
            supabase.table("investments").insert(payload).execute()
            # === 🧺 Update Inventory Table ===
            for item in ingredient_entries:
                name = item["ingredient"]
                qty = item["buy_qty"]
            
                existing = supabase.table("inventory") \
                    .select("id, quantity") \
                    .eq("team_name", st.session_state.team_name) \
                    .eq("resource_name", name) \
                    .eq("category", "ingredient") \
                    .execute()
            
                if existing.data:
                    new_qty = existing.data[0]["quantity"] + qty
                    supabase.table("inventory").update({
                        "quantity": new_qty,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", existing.data[0]["id"]).execute()
                else:
                    supabase.table("inventory").insert({
                        "team_name": st.session_state.team_name,
                        "category": "ingredient",
                        "resource_name": name,
                        "quantity": qty,
                        "unit": item["unit"]
                    }).execute()
            
            
            for item in capacity_entries:
                name = item["parameter"].replace("_wage_usd_per_hour", "").replace("_usd_per_hour", "").replace("_wage", "").replace("_", " ").title()

                qty = item["hours"]
            
                existing = supabase.table("inventory") \
                    .select("id, quantity") \
                    .eq("team_name", st.session_state.team_name) \
                    .eq("resource_name", name) \
                    .eq("category", "capacity") \
                    .execute()
            
                if existing.data:
                    new_qty = existing.data[0]["quantity"] + qty
                    supabase.table("inventory").update({
                        "quantity": new_qty,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", existing.data[0]["id"]).execute()
                else:
                    supabase.table("inventory").insert({
                        "team_name": st.session_state.team_name,
                        "category": "capacity",
                        "resource_name": name,
                        "quantity": qty,
                        "unit": "hours"
                    }).execute()
            # Compute new balance and update team
            new_balance = remaining_budget - total_investment
            supabase.table("teams").update({"money": new_balance}).eq(
                "team_name", st.session_state.team_name
            ).execute()
    
            # Update session and confirm
            st.session_state.money = new_balance
            st.success(f"✅ Investment saved! Remaining balance: ${new_balance:,.2f}")
    
        except Exception as e:
            st.error("❌ Failed to save to Supabase.")
            st.exception(e)


# ============================
# 📜 INVESTMENT HISTORY
# ============================
st.markdown("---")
st.subheader("📜 Daily Investment Summary")

try:
    response = (
        supabase.table("investments")
        .select("*")
        .eq("team_name", st.session_state.team_name)
        .order("inserted_at", desc=True)
        .execute()
    )
    investments = response.data

    if not investments:
        st.info("No previous investments found yet.")
    else:
        inv_df = pd.DataFrame(investments)
        inv_df["date"] = pd.to_datetime(inv_df["inserted_at"]).dt.date

        # Group by day
        for day, group in inv_df.groupby("date", sort=False):
            total_day_cost = group["total_cost_usd"].sum()

            # Only show days where total cost > 0
            if total_day_cost <= 0:
                continue

            with st.expander(f"📅 {day.strftime('%B %d, %Y')} — Total Spent: ${total_day_cost:,.2f}"):
                all_ingredients = []
                all_capacity = []

                for _, inv in group.iterrows():
                    try:
                        ing = json.loads(inv["ingredients_json"])
                        cap = json.loads(inv["capacity_json"])
                        all_ingredients.extend(ing)
                        all_capacity.extend(cap)
                    except Exception:
                        continue

                # Filter out zero-quantity ingredients
                if all_ingredients:
                    ing_df = pd.DataFrame(all_ingredients)
                    ing_df = ing_df[(ing_df["buy_qty"] > 0) & (ing_df["subtotal_usd"] > 0)]
                    if not ing_df.empty:
                        st.markdown("**🧺 Ingredients Purchased:**")
                        ing_df = ing_df.groupby("ingredient", as_index=False)[["buy_qty", "subtotal_usd"]].sum()
                        ing_df["subtotal_usd"] = ing_df["subtotal_usd"].round(2)
                        st.dataframe(ing_df, use_container_width=True)

                # Filter out zero-hour capacity purchases
                if all_capacity:
                    cap_df = pd.DataFrame(all_capacity)
                    cap_df = cap_df[(cap_df["hours"] > 0) & (cap_df["subtotal_usd"] > 0)]
                    if not cap_df.empty:
                        st.markdown("**🏭 Capacity Purchased:**")
                        if "parameter" in cap_df.columns:
                            cap_df["parameter"] = cap_df["parameter"].apply(
                                lambda x: x.replace("_usd_per_hour", "")
                                          .replace("_wage", "")
                                          .replace("_", " ")
                                          .title()
                            )
                        cap_df = cap_df.groupby("parameter", as_index=False)[["hours", "subtotal_usd"]].sum()
                        cap_df["subtotal_usd"] = cap_df["subtotal_usd"].round(2)
                        st.dataframe(cap_df, use_container_width=True)

                if (not all_ingredients) and (not all_capacity):
                    st.info("No valid purchases for this day.")

except Exception as e:
    st.error("❌ Failed to load investment history.")
    st.exception(e)






if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success("You’ve been logged out.")
    st.switch_page("Login.py")