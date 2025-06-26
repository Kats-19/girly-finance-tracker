# --- STYLING --- #
def set_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&family=Caveat&display=swap');

    html, body, .stApp {
        background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%);
        font-family: 'Quicksand', sans-serif;
        color: white;
    }

    h1, h2, h3, h4 {
        color: white !important;
    }

    .stButton>button {
        background-color: #ff69b4;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 600;
    }

    .stButton>button:hover {
        background-color: #e85d9e;
        color: white;
    }

    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stNumberInput>div>input,
    .stTextArea textarea {
        background-color: #ffb6c1;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        border: none;
        padding: 8px;
    }

    .stTextInput>div>div>input::placeholder,
    .stTextArea textarea::placeholder {
        color: #ffe4e1;
    }

    .stSidebar {
        background-color: #ffe0ec;
        color: white;
    }

    .css-1v0mbdj.edgvbvh3 {
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

import os
import io
import random
import datetime
import calendar

import pandas as pd
import streamlit as st
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

set_styles()

# Set up connection to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

import json
import streamlit as st
secrets = st.secrets

gcp_secrets = dict(secrets["gcp_service_account"])
gcp_secrets["private_key"] = gcp_secrets["private_key"].replace("\\n", "\n")
creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scope)

client = gspread.authorize(creds)

# Open your Google Sheet by name
sheet = client.open("Budget Data").sheet1  # opens the first sheet (you can rename later)

def save_to_google_sheet(name, year, month, type_, category, amount, notes=""):
    row = [name, year, month, type_, category, amount, notes]
    sheet.append_row(row)

# ---------------- LOGIN SIMULATION ---------------- #
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Girlboss Finance Tracker Login")
    name_input = st.text_input("Enter your name")
    password_input = st.text_input("Enter your passcode", type="password")

    if st.button("Login"):
        # You can change this logic to allow real password checking later
        if password_input == "pass123":
            st.session_state.authenticated = True
            st.session_state.user_name = name_input or "Budget Babe"
            st.experimental_rerun()
        else:
            st.error("Oops! Wrong passcode, queen 👑")

    st.stop()  # Prevents app from running further until logged in

st.set_page_config(page_title="Girly Budget Tracker 💖", layout="centered")

st.title("✨Girly Finance Tracker✨")
st.markdown("Track your income, budget, and expenses like the queen you are 👑")

# --- MONTH --- #
st.sidebar.header("📆 Select Month")
selected_year = st.sidebar.selectbox("Year", list(range(2023, datetime.datetime.now().year + 1)), index=1)
selected_month = st.sidebar.selectbox("Month", list(calendar.month_name[1:]), index=datetime.datetime.now().month - 1)
filter_key = f"{selected_month}_{selected_year}"

st.markdown(f"### 📒 Viewing data for {selected_month} {selected_year}")

# --- SESSION STATE: Expenses --- #
if "all_expenses" not in st.session_state:
    st.session_state.all_expenses = {}

if filter_key not in st.session_state.all_expenses:
    st.session_state.all_expenses[filter_key] = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

# --- SESSION STATE: Income --- #
if "all_income" not in st.session_state:
    st.session_state.all_income = {}

if filter_key not in st.session_state.all_income:
    st.session_state.all_income[filter_key] = pd.DataFrame(columns=["Date", "Source", "Amount"])

# --- SESSION STATE --- #
if "all_expenses" not in st.session_state:
    st.session_state.all_expenses = {}

folder_name = "Saved Budgets"
os.makedirs(folder_name, exist_ok=True)
file_path = os.path.join(folder_name, f"{selected_month}_{selected_year}_Budget.xlsx")

if filter_key not in st.session_state.all_expenses:
    if os.path.exists(file_path):
        try:
            # Load the Expenses sheet if the file exists
            loaded_data = pd.read_excel(file_path, sheet_name="Expenses")
            st.session_state.all_expenses[filter_key] = loaded_data
            st.success("✅ Previous budget data loaded!")
        except Exception as e:
            st.warning(f"Could not load saved data: {e}")
            st.session_state.all_expenses[filter_key] = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
    else:
        st.session_state.all_expenses[filter_key] = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

current_expenses = st.session_state.all_expenses[filter_key]

# Ensure expected columns exist after loading
expected_columns = ["Date", "Category", "Amount", "Description"]
for col in expected_columns:
    if col not in current_expenses.columns:
        current_expenses[col] = ""

# --- INPUTS --- #
# --- INCOME SECTION --- #
st.markdown("### 💰 Add Income")

income_df = st.session_state.all_income[filter_key]

income_date = st.date_input("Income Date", datetime.date.today(), key="income_date")
income_source = st.text_input("Income Source", key="income_source")
income_amount = st.number_input("Income Amount (€)", min_value=0.0, step=10.0, key="income_amount")

if st.button("Add Income"):
    new_income = {
        "Date": income_date,
        "Source": income_source,
        "Amount": income_amount
    }
    income_df = pd.concat([income_df, pd.DataFrame([new_income])], ignore_index=True)
    st.session_state.all_income[filter_key] = income_df
    st.success("Income added!")

if not income_df.empty:
    st.markdown("### 📋 Your Income")
    income_df["Date"] = pd.to_datetime(income_df["Date"], errors="coerce")
    st.dataframe(income_df)

total_income = income_df["Amount"].sum()
budget = st.number_input("Set your monthly budget (€)", min_value=0.0, step=50.0)

st.markdown("### 💸 Add Expenses")
category = st.selectbox("Category", ["Food", "Shopping", "School", "Transport", "Fun", "Other"])
amount = st.number_input("Amount (€)", min_value=0.0, step=1.0)
description = st.text_input("Description")
date = st.date_input("Date", datetime.date.today())

if st.button("Add Expense"):
    new_entry = {
        "Date": date,
        "Category": category,
        "Amount": amount,
        "Description": description
    }
    current_expenses = pd.concat([current_expenses, pd.DataFrame([new_entry])], ignore_index=True)
    st.session_state.all_expenses[filter_key] = current_expenses
    st.success("Expense added!")

# --- DISPLAY EXPENSES --- #
if "Date" in current_expenses.columns:
    current_expenses["Date"] = pd.to_datetime(current_expenses["Date"])
    
st.markdown("### 🧮 Your Expenses")
st.dataframe(current_expenses)

total_spent = current_expenses["Amount"].sum()
remaining_budget = budget - total_spent
savings = total_income - total_spent

st.markdown(f"**Total Spent:** €{total_spent:.2f}")
st.markdown(f"**Remaining Budget:** €{remaining_budget:.2f}")
st.markdown(f"**Estimated Savings:** €{savings:.2f}")

# --- PROGRESS BAR --- #
st.markdown("### ⏳ Budget Progress")
if budget > 0:
    percent_used = min(total_spent / budget, 1.0)
    st.progress(percent_used, text=f"{percent_used * 100:.0f}% of your budget used")
    if percent_used < 0.5:
        st.success("You're doing amazing, sweetie! 💖")
    elif percent_used < 0.9:
        st.warning("Watch it, queen 🙀 You're getting close!")
    else:
        st.error("Budget crisis! Time to pause the shopping carts ⏹️🛍️")
else:
    st.info("Set a budget above to see progress.")

# --- PIE CHART --- #
if not current_expenses.empty:
    st.markdown("### 📊 Where Your Money Goes")
    category_totals = current_expenses.groupby("Category")["Amount"].sum().reset_index()
    fig = px.pie(category_totals, values="Amount", names="Category", title="Expenses by Category", color_discrete_sequence=px.colors.sequential.Pinkyl)
    st.plotly_chart(fig, use_container_width=True)


# --- INSPIRATIONAL QUOTE OF THE MONTH --- #
st.markdown("## 🌷 Quote of the Month")
quotes = [
    "\"A budget is telling your money where to go instead of wondering where it went.\" – Dave Ramsey",
    "\"You deserve to feel in control of your finances and your future.\"",
    "\"Small savings today, big dreams tomorrow 💖\"",
    "\"Financial wellness is self-care. Period.\"",
    "\"Treat your money like you treat your bestie — with love and boundaries.\""
]
random.seed(f"{selected_month}_{selected_year}")
monthly_quote = random.choice(quotes)

st.markdown(f"> *{monthly_quote}*")

st.markdown("### 💌 Monthly Notes & Reflections")

notes_key = f"notes_{filter_key}"
if "monthly_notes" not in st.session_state:
    st.session_state.monthly_notes = {}

saved_note = st.session_state.monthly_notes.get(notes_key, "")

# Prompts
with st.expander("🧠 Need help? Try these prompts:"):
    st.markdown("""
    - What did I do well this month with my money?
    - Where did I overspend (and why)?
    - What’s one thing I want to improve next month?
    - What’s my money mantra this month?
    """)

note = st.text_area("Write your thoughts, goals, or money mindset vibes:", value=saved_note, height=200)

if st.button("Save Note ✨"):
    st.session_state.monthly_notes[notes_key] = note
    st.success("Note saved for this month 💖")


# --- EXPORT TO EXCEL --- #
st.markdown("### 📅 Export Your Budget to Excel")
if not current_expenses.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        current_expenses.to_excel(writer, sheet_name="Expenses", index=False)
        summary_df = pd.DataFrame({
            "Metric": ["Income", "Budget", "Total Spent", "Remaining Budget", "Estimated Savings"],
            "Amount (€)": [total_income, budget, total_spent, remaining_budget, savings]
        })
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        workbook = writer.book
        summary_ws = writer.sheets["Summary"]
        expenses_ws = writer.sheets["Expenses"]

        header_format = workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#ff69b4', 'border': 1
        })

        for col in range(summary_df.shape[1]):
            summary_ws.write(0, col, summary_df.columns[col], header_format)
            summary_ws.set_column(col, col, 20)

        for col in range(current_expenses.shape[1]):
            expenses_ws.write(0, col, current_expenses.columns[col], header_format)
            expenses_ws.set_column(col, col, 20)

    st.markdown("### 💾 Auto-Saving Your Budget to Excel")

if not current_expenses.empty:
    folder_name = "Saved Budgets"
    os.makedirs(folder_name, exist_ok=True)

    file_path = os.path.join(folder_name, f"{selected_month}_{selected_year}_Budget.xlsx")

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        current_expenses.to_excel(writer, sheet_name="Expenses", index=False)

        summary_df = pd.DataFrame({
            "Metric": ["Income", "Budget", "Total Spent", "Remaining Budget", "Estimated Savings"],
            "Amount (€)": [total_income, budget, total_spent, remaining_budget, savings]
        })
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        workbook = writer.book
        summary_ws = writer.sheets["Summary"]
        expenses_ws = writer.sheets["Expenses"]

        header_format = workbook.add_format({
            'bold': True, 'font_color': 'white',
            'bg_color': '#ff69b4', 'border': 1
        })

        for col in range(summary_df.shape[1]):
            summary_ws.write(0, col, summary_df.columns[col], header_format)
            summary_ws.set_column(col, col, 20)

        for col in range(current_expenses.shape[1]):
            expenses_ws.write(0, col, current_expenses.columns[col], header_format)
            expenses_ws.set_column(col, col, 20)

    st.success(f"Auto-saved to: `{file_path}`")
else:
    st.info("No expenses added yet to save.")
