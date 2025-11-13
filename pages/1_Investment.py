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

GAME_START_DATE = os.getenv("GAME_START_DATE", "2025-11-13")
start_date = datetime.strptime(GAME_START_DATE, "%Y-%m-%d").date()
today = date.today()

# Ensure day_number never goes below 1 before the game starts
day_number = max(1, (today - start_date).days + 1)
st.session_state.day = day_number


# ✅ Handle reset triggered after save
if st.session_state.get("reset_tables", False):
    if "ingredients_table" in st.session_state:
        import pandas as pd
        try:
            raw_data = st.session_state.ingredients_table
            if isinstance(raw_data, dict) and "data" in raw_data:
                raw_data = raw_data["data"]
            df = pd.DataFrame(raw_data)
            if "Enter value" in df.columns:
                df["Enter value"] = 0.0
            st.session_state.ingredients_table = df.to_dict("records")
        except Exception:
            pass

    for key in list(st.session_state.keys()):
        if key.startswith("cap_"):
            st.session_state[key] = 0.0

    # Reset the flag
    st.session_state.reset_tables = False


# ============================
# 🔒 LOGIN CHECK
# ============================
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
# 🎨 PAGE STYLING
# =====================================
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 10px !important;
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

    canvas {
        background-color: #FFF9F3 !important;
        border-radius: 12px;
    }

    .stButton>button[kind="secondary"] {
        background-color: #FFF2E0 !important;
        color: #4B2E05 !important;
        border: 1px solid #D6A76E !important;
    }

    /* ✅ Reliable Center Alignment for All Streamlit Tables */
    [data-testid="stDataEditor"] table,
    [data-testid="stDataFrame"] table {
        width: 100% !important;
        table-layout: fixed !important;
        text-align: center !important;
    }
    
    [data-testid="stDataEditor"] th,
    [data-testid="stDataFrame"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    
    [data-testid="stDataEditor"] td div,
    [data-testid="stDataFrame"] td div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    
    [data-testid="stDataEditor"] input {
        text-align: center !important;
    }
    
    [data-testid="stDataEditor"] td, 
    [data-testid="stDataFrame"] td {
        padding: 8px !important;
        vertical-align: middle !important;
    }

    /* 🧭 FORCE Center Alignment inside Streamlit’s Virtualized Table Cells */
    [data-testid="stDataEditor"] .st-emotion-cache,
    [data-testid="stDataFrame"] .st-emotion-cache,
    [data-testid="stDataEditor"] div[data-testid="cell-container"],
    [data-testid="stDataFrame"] div[data-testid="cell-container"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    
    /* Center text in all number inputs inside data editors */
    [data-testid="stDataEditor"] input {
        text-align: center !important;
    }
    
    /* Ensure editable columns have centered placeholders too */
    [data-testid="stDataEditor"] input::placeholder {
        text-align: center !important;
    }
    
    /* Optional: Fix width-based overflow alignment */
    [data-testid="stDataEditor"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="gridcell"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    /* ✅ Center alignment for Investment History tables (st.dataframe) */
    [data-testid="stDataFrame"] table {
        width: 100% !important;
        text-align: center !important;
        table-layout: fixed !important;
    }
    
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    
    /* Streamlit virtualized cell containers */
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[data-testid="cell-container"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    
    /* Optional: Center numbers inside scrollable or virtualized cells */
    [data-testid="stDataFrame"] input {
        text-align: center !important;
    }
    /* ✅ Center align headers and cells inside read-only data editors (investment history) */
    div[data-testid="stDataEditor"] thead tr th {
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
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
            📅 <span style="font-size:1.3rem;">Week {st.session_state.day}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("💰 Investment Decisions")
st.write(f"Welcome, **{st.session_state.team_name}**!")

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

valid_params = [
    "prep_wage_usd_per_hour",
    "oven_wage_usd_per_hour",
    "package_wage_usd_per_hour",
    "oven_rental_wage_usd_per_hour"
]
filtered_wages = wages[wages["parameter"].isin(valid_params)]

# ============================
# 💵 CASH AND STOCK VALUE
# ============================
inventory_data = (
    supabase.table("inventory")
    .select("resource_name, quantity")
    .eq("team_name", st.session_state.team_name)
    .eq("category", "ingredient")
    .execute()
)


# Build a dictionary of ingredient → quantity
current_stock = {i["resource_name"]: i["quantity"] for i in inventory_data.data} if inventory_data.data else {}

capacity_data = (
    supabase.table("inventory")
    .select("resource_name, quantity")
    .eq("team_name", st.session_state.team_name)
    .eq("category", "capacity")
    .execute()
)

capacity_stock = {i["resource_name"]: i["quantity"] for i in capacity_data.data} if capacity_data.data else {}

# Copy the ingredients CSV data
ingredients_df = ingredients.copy()

# Numeric stock column for calculations
ingredients_df["Current stock (num)"] = (
    ingredients_df["ingredient"]
    .map(current_stock)
    .fillna(0)
)

# String stock column for display (centering)
ingredients_df["Current stock"] = ingredients_df["Current stock (num)"].map(lambda x: f"{x:g}")

# ✅ Financial calculations use the numeric version
cash_value = st.session_state.money
# Ingredient stock value
ingredient_value = sum(ingredients_df["unit_cost_usd"] * ingredients_df["Current stock (num)"])

# Build a lookup for capacity unit cost from wages table
capacity_cost_lookup = {
    row["parameter"]
        .replace("_wage_usd_per_hour", "")
        .replace("_usd_per_hour", "")
        .replace("_wage", "")
        .replace("_", " ")
        .title(): float(row["value"])
    for _, row in filtered_wages.iterrows()
}

# Capacity stock value
capacity_value = sum(
    capacity_cost_lookup.get(cap_name, 0) * qty
    for cap_name, qty in capacity_stock.items()
)

# Total stock value (ingredients + capacity)
stock_value = ingredient_value + capacity_value

st.markdown(
    f"""
    <div style="display:flex; gap:40px; font-size:1.2rem; font-weight:700; color:#4B2E05;">
        <div>💵 Cash value: ${cash_value:,.2f}</div>
        <div>📦 Stock value: ${stock_value:,.2f}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================
# 🧺 INGREDIENTS SECTION
# ============================
st.subheader("🧺 Ingredients Purchase")

ingredients_df["Unit cost (unit)"] = ingredients_df.apply(
    lambda x: f"${x['unit_cost_usd']:.2f} ({x['unit']})", axis=1
)
ingredients_df["Enter value"] = 0.0

ingredients_display = ingredients_df[["ingredient", "Unit cost (unit)", "Current stock", "Enter value"]]
ingredients_display = ingredients_display.rename(columns={"ingredient": "Ingredient"})

st.markdown("Enter the quantities you want to buy below:")
edited_df = st.data_editor(
    ingredients_display,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="ingredients_table",
    column_config={
        "Ingredient": {
            "disabled": True,
            "alignment": "center",
        },
        "Unit cost (unit)": {
            "disabled": True,
            "alignment": "center",
        },
        "Current stock": {
            "disabled": True,
            "alignment": "center",
        },
        "Enter value": {
            "type": "number",
            "min_value": 0.0,
            "step": 0.5,
            "alignment": "center",
        },
    },
)


merged = ingredients.merge(edited_df, left_on="ingredient", right_on="Ingredient")
merged["subtotal_usd"] = merged["Enter value"] * merged["unit_cost_usd"]
total_ingredients_cost = merged["subtotal_usd"].sum()

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
# 🏭 PRODUCTION CAPACITY
# ============================
st.subheader("🏭 Production Capacity")
capacity_entries = []
total_capacity_cost = 0.0


header_cols = st.columns([3, 2, 2])
header_cols[0].markdown("**Capacity Type**")
header_cols[1].markdown("**Rate (USD/hr)**")
header_cols[2].markdown("**Hours to Buy**")

for idx, row in filtered_wages.iterrows():
    param = row["parameter"]
    rate = float(row["value"])
    label = param.replace("_wage_usd_per_hour", "").replace("_usd_per_hour", "").replace("_wage", "").replace("_", " ").title()

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
        "parameter": param,
        "display_name": label,
        "unit_cost_usd": rate,
        "hours": hours,
        "subtotal_usd": subtotal
    })

st.markdown(f"**Total Capacity Cost:** ${total_capacity_cost:,.2f}")

# ============================
# 📈 SUMMARY
# ============================
st.markdown("---")
team_data = supabase.table("teams").select("money").eq("team_name", st.session_state.team_name).execute()
if team_data.data:
    current_balance = team_data.data[0]["money"]
    st.session_state.money = current_balance
else:
    current_balance = st.session_state.money

total_investment = total_ingredients_cost + total_capacity_cost
remaining = current_balance - total_investment

col1, col2, col3 = st.columns(3)
col1.metric("Cash Value", f"${cash_value:,.2f}")
col2.metric("Total Investment", f"${total_investment:,.2f}")
col3.metric("Remaining After Purchase", f"${remaining:,.2f}")

# ============================
# 💾 SAVE TO SUPABASE
# ============================
# ============================
# 💾 SAVE TO SUPABASE (with confirmation)
# ============================
if total_investment > current_balance:
    st.error("⚠️ You exceeded your budget! Please adjust your quantities.")
else:
    # Confirmation flag
    if "confirm_investment" not in st.session_state:
        st.session_state.confirm_investment = False

    if st.button("💾 Save Investment"):
        if total_investment == 0:
            st.warning("⚠️ Please enter some investment before saving.")
        else:
            st.session_state.confirm_investment = True
            st.rerun()

    if st.session_state.confirm_investment:
        st.warning("⚠️ Are you sure you want to save these investment decisions?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, save now"):
                try:
                    # 1️⃣ Record investment details
                    payload = {
                        "team_name": st.session_state.team_name,
                        "ingredients_json": json.dumps(ingredient_entries),
                        "capacity_json": json.dumps(capacity_entries),
                        "total_cost_usd": total_investment,
                    }
                    supabase.table("investments").insert(payload).execute()

                    # 2️⃣ Update ingredient inventory
                    for item in ingredient_entries:
                        name = item["ingredient"]
                        qty = item["buy_qty"]
                        existing = (
                            supabase.table("inventory")
                            .select("id, quantity")
                            .eq("team_name", st.session_state.team_name)
                            .eq("resource_name", name)
                            .eq("category", "ingredient")
                            .execute()
                        )
                        if existing.data:
                            new_qty = existing.data[0]["quantity"] + qty
                            supabase.table("inventory").update(
                                {"quantity": new_qty}
                            ).eq("id", existing.data[0]["id"]).execute()
                        else:
                            supabase.table("inventory").insert({
                                "team_name": st.session_state.team_name,
                                "category": "ingredient",
                                "resource_name": name,
                                "quantity": qty,
                                "unit": item["unit"]
                            }).execute()

                    # 3️⃣ Update capacity inventory
                    for item in capacity_entries:
                        name = item["parameter"].replace("_wage_usd_per_hour", "").replace("_usd_per_hour", "").replace("_wage", "").replace("_", " ").title()
                        qty = item["hours"]
                        existing = (
                            supabase.table("inventory")
                            .select("id, quantity")
                            .eq("team_name", st.session_state.team_name)
                            .eq("resource_name", name)
                            .eq("category", "capacity")
                            .execute()
                        )
                        if existing.data:
                            new_qty = existing.data[0]["quantity"] + qty
                            supabase.table("inventory").update(
                                {"quantity": new_qty}
                            ).eq("id", existing.data[0]["id"]).execute()
                        else:
                            supabase.table("inventory").insert({
                                "team_name": st.session_state.team_name,
                                "category": "capacity",
                                "resource_name": name,
                                "quantity": qty,
                                "unit": "hours"
                            }).execute()

                    # 4️⃣ Update team financials
                    team_resp = (
                        supabase.table("teams")
                        .select("money, stock_value")
                        .eq("team_name", st.session_state.team_name)
                        .execute()
                    )
                    if team_resp.data:
                        team_data = team_resp.data[0]
                        current_money = float(team_data.get("money", 0.0))
                        current_stock = float(team_data.get("stock_value", 0.0))
                        new_money = current_money - total_investment
                        new_stock = current_stock + total_investment
                        supabase.table("teams").update(
                            {"money": new_money, "stock_value": new_stock}
                        ).eq("team_name", st.session_state.team_name).execute()

                        # ✅ Update session state immediately
                        st.session_state.money = new_money
                        st.session_state.stock_value = new_stock

                    st.success(f"✅ Investment saved! Remaining balance: ${new_money:,.2f}")
                    st.info(f"📦 Updated stock value: ${new_stock:,.2f}")

                    st.session_state.confirm_investment = False
                    st.session_state.reset_tables = True
                    st.rerun()

                except Exception as e:
                    st.error("❌ Failed to save to Supabase.")
                    st.exception(e)

        with col2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_investment = False
                st.info("Investment save cancelled.")


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
        for day, group in inv_df.groupby("date", sort=False):
            total_day_cost = group["total_cost_usd"].sum()
            if total_day_cost <= 0:
                continue
            
            with st.expander(f"📅 {day.strftime('%B %d, %Y')} — Total Spent: ${total_day_cost:,.2f}"):
                all_ingredients, all_capacity = [], []
        
                # Collect all ingredient & capacity records for that day
                for _, inv in group.iterrows():
                    try:
                        all_ingredients.extend(json.loads(inv["ingredients_json"]))
                        all_capacity.extend(json.loads(inv["capacity_json"]))
                    except Exception:
                        continue
        
                # ============================
                # 🧺 INGREDIENTS PURCHASED (centered + unit)
                # ============================
                if all_ingredients:
                    ing_df = pd.DataFrame(all_ingredients)
                    ing_df = ing_df[(ing_df["buy_qty"] > 0) & (ing_df["subtotal_usd"] > 0)]
                
                    if not ing_df.empty:
                        st.markdown("**🧺 Ingredients Purchased:**")
                
                        # Ingredient (unit) column, e.g. "Cocoa Powder (kg)"
                        ing_df["Ingredient (unit)"] = ing_df.apply(
                            lambda x: f"{x['ingredient']} ({x['unit']})",
                            axis=1,
                        )
                
                        # Build ordered ingredient labels based on ingredients.csv
                        ingredient_order = [
                            f"{row['ingredient']} ({row['unit']})"
                            for _, row in ingredients.iterrows()
                        ]
                
                        # Group and sum
                        ing_grouped = (
                            ing_df.groupby("Ingredient (unit)", as_index=False)[["buy_qty", "subtotal_usd"]]
                                 .sum()
                        )
                
                        # Reorder according to CSV order
                        ing_display = (
                            ing_grouped.set_index("Ingredient (unit)")
                                       .reindex(ingredient_order)
                                       .dropna(how="all")
                                       .reset_index()
                        )
                
                        # Round subtotal before renaming
                        ing_display["subtotal_usd"] = ing_display["subtotal_usd"].round(2)
                
                        # Rename columns for pretty header
                        ing_display = ing_display.rename(
                            columns={
                                "Ingredient (unit)": "Ingredient",
                                "buy_qty": "Quantity",
                                "subtotal_usd": "Subtotal (USD)",
                            }
                        )
                
                        # Format numeric columns as strings for centering
                        ing_display["Quantity"] = ing_display["Quantity"].map(lambda x: f"{x:g}")
                        ing_display["Subtotal (USD)"] = ing_display["Subtotal (USD)"].map(
                            lambda x: f"${x:,.2f}"
                        )
                
                        st.data_editor(
                            ing_display,
                            use_container_width=True,
                            hide_index=True,
                            disabled=True,
                            key=f"history_ing_{day.isoformat()}",
                            column_config={
                                "Ingredient": {"alignment": "center"},
                                "Quantity": {"alignment": "center"},
                                "Subtotal (USD)": {"alignment": "center"},
                            },
                        )


        
                # ============================
                # 🏭 CAPACITY PURCHASED (centered + hours)
                # ============================
                if all_capacity:
                    cap_df = pd.DataFrame(all_capacity)
                    cap_df = cap_df[(cap_df["hours"] > 0) & (cap_df["subtotal_usd"] > 0)]
                
                    if not cap_df.empty:
                        st.markdown("**🏭 Capacity Purchased:**")
                
                        # Human label + unit, e.g. "Oven (hours)"
                        cap_df["Capacity (unit)"] = cap_df["parameter"].apply(
                            lambda x: x.replace("_usd_per_hour", "")
                                      .replace("_wage", "")
                                      .replace("_", " ")
                                      .title() + " (hours)"
                        )
                
                        # Build ordered capacity labels based on wages_energy.csv
                        capacity_order = [
                            row["parameter"]
                                .replace("_usd_per_hour", "")
                                .replace("_wage", "")
                                .replace("_", " ")
                                .title() + " (hours)"
                            for _, row in filtered_wages.iterrows()
                        ]
                
                        # Group and sum
                        cap_grouped = (
                            cap_df.groupby("Capacity (unit)", as_index=False)[["hours", "subtotal_usd"]]
                                 .sum()
                        )
                
                        # Reorder according to CSV order
                        cap_display = (
                            cap_grouped.set_index("Capacity (unit)")
                                       .reindex(capacity_order)
                                       .dropna(how="all")
                                       .reset_index()
                        )
                
                        # Round subtotal before renaming
                        cap_display["subtotal_usd"] = cap_display["subtotal_usd"].round(2)
                
                        # Rename columns for pretty header
                        cap_display = cap_display.rename(
                            columns={
                                "Capacity (unit)": "Capacity",
                                "hours": "Hours Purchased",
                                "subtotal_usd": "Subtotal (USD)",
                            }
                        )
                
                        # Format numeric columns as strings for centering
                        cap_display["Hours Purchased"] = cap_display["Hours Purchased"].map(lambda x: f"{x:g}")
                        cap_display["Subtotal (USD)"] = cap_display["Subtotal (USD)"].map(
                            lambda x: f"${x:,.2f}"
                        )
                
                        st.data_editor(
                            cap_display,
                            use_container_width=True,
                            hide_index=True,
                            disabled=True,
                            key=f"history_cap_{day.isoformat()}",
                            column_config={
                                "Capacity": {"alignment": "center"},
                                "Hours Purchased": {"alignment": "center"},
                                "Subtotal (USD)": {"alignment": "center"},
                            },
                        )




except Exception as e:
    st.error("❌ Failed to load investment history.")
    st.exception(e)

# ============================
# 🔁 REVOKE TODAY'S INVESTMENT (only if production not submitted)
st.markdown("---")
st.subheader("🔁 Revoke Today's Investment")

try:
    # 1️⃣ Check if production plan exists for today
    prod_check = (
        supabase.table("production_plans")
        .select("id")
        .eq("team_name", st.session_state.team_name)
        .eq("day_number", day_number)
        .execute()
    )

    has_production = bool(prod_check.data)

    # 2️⃣ Get today's investments
    inv_check = (
        supabase.table("investments")
        .select("*")
        .eq("team_name", st.session_state.team_name)
        .gte("inserted_at", f"{date.today().isoformat()}T00:00:00")
        .execute()
    )

    if not inv_check.data:
        st.info("No investments found for today.")
    elif has_production:
        st.warning("⚠️ You’ve already submitted your production plan — revoking investments is no longer allowed.")
    else:
        total_today_cost = sum(inv["total_cost_usd"] for inv in inv_check.data)
        st.info(f"💰 You invested **${total_today_cost:,.2f}** today.")

        if st.button("🚫 Revoke Today's Investment"):
            try:
                # Roll back team finances
                team_resp = (
                    supabase.table("teams")
                    .select("money, stock_value")
                    .eq("team_name", st.session_state.team_name)
                    .execute()
                )
                if team_resp.data:
                    team = team_resp.data[0]
                    new_money = float(team["money"]) + total_today_cost
                    new_stock = float(team["stock_value"]) - total_today_cost

                    supabase.table("teams").update(
                        {"money": new_money, "stock_value": new_stock}
                    ).eq("team_name", st.session_state.team_name).execute()

                    # ✅ ALSO update session state so Cash Value updates immediately
                    st.session_state.money = new_money
                    st.session_state.stock_value = new_stock

                # Roll back inventory for ingredients & capacity
                for inv in inv_check.data:
                    for ing in json.loads(inv["ingredients_json"]):
                        name = ing["ingredient"]
                        qty = float(ing["buy_qty"])
                        if qty > 0:
                            inv_data = (
                                supabase.table("inventory")
                                .select("id, quantity")
                                .eq("team_name", st.session_state.team_name)
                                .eq("resource_name", name)
                                .eq("category", "ingredient")
                                .execute()
                            )
                    
                            if inv_data.data:
                                row = inv_data.data[0]
                                # 👇 make sure we work with floats, not Decimal/str
                                current_qty = float(row.get("quantity") or 0)
                                new_qty = current_qty - qty
                    
                                if new_qty <= 0:
                                    # 🔥 actually remove the row from inventory
                                    supabase.table("inventory").delete().eq("id", row["id"]).execute()
                                else:
                                    supabase.table("inventory").update(
                                        {"quantity": new_qty}
                                    ).eq("id", row["id"]).execute()

                  
                    for cap in json.loads(inv["capacity_json"]):
                        name = (
                            cap["parameter"]
                            .replace("_wage_usd_per_hour", "")
                            .replace("_usd_per_hour", "")
                            .replace("_wage", "")
                            .replace("_", " ")
                            .title()
                        )
                        qty = float(cap["hours"])
                        if qty > 0:
                            inv_data = (
                                supabase.table("inventory")
                                .select("id, quantity")
                                .eq("team_name", st.session_state.team_name)
                                .eq("resource_name", name)
                                .eq("category", "capacity")
                                .execute()
                            )
                    
                            if inv_data.data:
                                row = inv_data.data[0]
                                current_qty = float(row.get("quantity") or 0)
                                new_qty = current_qty - qty
                    
                                if new_qty <= 0:
                                    supabase.table("inventory").delete().eq("id", row["id"]).execute()
                                else:
                                    supabase.table("inventory").update(
                                        {"quantity": new_qty}
                                    ).eq("id", row["id"]).execute()

                # Delete today's investment records
                for inv in inv_check.data:
                    supabase.table("investments").delete().eq("id", inv["id"]).execute()

                st.success("✅ Today's investments successfully revoked!")
                st.rerun()

            except Exception as e:
                st.error("❌ Failed to revoke investments.")
                st.exception(e)

except Exception as e:
    st.error("❌ Could not check revocation status.")
    st.exception(e)



# ============================
# 🚪 LOGOUT
# ============================
if st.button("🚪 Log out"):
    st.session_state.clear()
    st.success
