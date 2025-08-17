# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ========================
# 📌 Database Setup
# ========================
DB_FILE = "food_donations.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

def run_sql(q, params=None):
    return pd.read_sql_query(q, conn, params=params)

today = date.today().strftime('%Y-%m-%d')

# ========================
# 🌐 Streamlit Layout
# ========================
st.set_page_config(page_title="🍽️ Food Donation Management", layout="wide")
st.title("🍽️ Food Donation Management System")

# Sidebar Filters
st.sidebar.header("🔍 Filter Donations")
city_filter = st.sidebar.text_input("Filter by Location (City)")
provider_filter = st.sidebar.text_input("Filter by Provider Name")
food_type_filter = st.sidebar.text_input("Filter by Food Type")

query = "SELECT * FROM Food_Listings WHERE 1=1"
params = []
if city_filter:
    query += " AND Location LIKE ?"
    params.append(f"%{city_filter}%")
if provider_filter:
    query += " AND Provider_ID IN (SELECT Provider_ID FROM Providers WHERE Name LIKE ?)"
    params.append(f"%{provider_filter}%")
if food_type_filter:
    query += " AND Food_Type LIKE ?"
    params.append(f"%{food_type_filter}%")

# ========================
# 📦 Filtered Food Listings
# ========================
st.subheader("📦 Filtered Food Listings")
try:
    filtered = run_sql(query, params)
    st.dataframe(filtered)
except Exception as e:
    st.warning(f"⚠️ {e}")

# ========================
# 📞 Contact Directory
# ========================
st.subheader("📞 Contact Directory")
tab1, tab2 = st.tabs(["Providers", "Receivers"])

with tab1:
    provs = run_sql("SELECT Provider_ID, Name, Provider_Type, Contact, City FROM Providers")
    st.dataframe(provs)

with tab2:
    recvs = run_sql("SELECT Receiver_ID, Name, Contact, City FROM Receivers")
    st.dataframe(recvs)

# ========================
# ✏️ CRUD Operations
# ========================
st.subheader("✏️ Manage Food Listings")
crud_choice = st.radio("Choose operation", ["Create", "Update", "Delete", "Read"])

if crud_choice == "Create":
    with st.form("create_food"):
        food_id = st.number_input("Food ID", step=1)
        name = st.text_input("Food Name")
        ftype = st.text_input("Food Type")
        mtype = st.text_input("Meal Type")
        qty = st.number_input("Quantity", step=1)
        expiry = st.date_input("Expiry Date").strftime('%Y-%m-%d')
        pid = st.number_input("Provider ID", step=1)
        loc = st.text_input("Location")
        submit = st.form_submit_button("Add Food")
        if submit:
            cursor.execute(
                """INSERT INTO Food_Listings VALUES (?,?,?,?,?,?,?,?)""",
                (food_id, name, ftype, mtype, qty, expiry, pid, loc),
            )
            conn.commit()
            st.success("✅ Food added!")

elif crud_choice == "Update":
    fid = st.number_input("Food ID to update", step=1)
    new_qty = st.number_input("New Quantity", step=1)
    if st.button("Update"):
        cursor.execute("UPDATE Food_Listings SET Quantity=? WHERE Food_ID=?", (new_qty, fid))
        conn.commit()
        st.success("✅ Updated!")

elif crud_choice == "Delete":
    fid = st.number_input("Food ID to delete", step=1)
    if st.button("Delete"):
        cursor.execute("DELETE FROM Food_Listings WHERE Food_ID=?", (fid,))
        conn.commit()
        st.success("✅ Deleted!")

elif crud_choice == "Read":
    st.dataframe(run_sql("SELECT * FROM Food_Listings LIMIT 20"))

# ========================
# 📊 Analytics
# ========================
st.subheader("📊 Analytics & Insights")
queries = {
    "Providers vs Receivers by City": """
        SELECT City, COUNT(*) FILTER (WHERE tbl='Providers') AS Providers,
               COUNT(*) FILTER (WHERE tbl='Receivers') AS Receivers,
               COUNT(*) AS Total
        FROM (
          SELECT City, 'Providers' AS tbl FROM Providers
          UNION ALL
          SELECT City, 'Receivers' AS tbl FROM Receivers
        )
        GROUP BY City
        ORDER BY Total DESC
        LIMIT 10;
    """,
    "Top Provider Types by Quantity": """
        SELECT p.Provider_Type, SUM(f.Quantity) AS Total_Quantity
        FROM Food_Listings f
        JOIN Providers p ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Provider_Type
        ORDER BY Total_Quantity DESC
        LIMIT 10;
    """,
    "Top Receivers by Claims": """
        SELECT r.Receiver_ID, r.Name, COUNT(*) AS Claim_Count
        FROM Claims c
        JOIN Receivers r ON r.Receiver_ID = c.Receiver_ID
        GROUP BY r.Receiver_ID, r.Name
        ORDER BY Claim_Count DESC
        LIMIT 10;
    """,
    "Total Food Available": """
        SELECT SUM(Quantity) AS Total_Quantity FROM Food_Listings;
    """,
    "Most Common Food Types": """
        SELECT Food_Type, COUNT(*) AS Count_Listings
        FROM Food_Listings
        GROUP BY Food_Type
        ORDER BY Count_Listings DESC
        LIMIT 10;
    """,
    "Claims Per Food Item": """
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claims
        FROM Food_Listings f
        LEFT JOIN Claims c ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
        ORDER BY Claims DESC
        LIMIT 10;
    """,
    "Total Quantity by Provider": """
        SELECT p.Name, SUM(f.Quantity) AS Total_Quantity
        FROM Food_Listings f
        JOIN Providers p ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Name
        ORDER BY Total_Quantity DESC
        LIMIT 10;
    """,
    "Claims by City": """
        SELECT f.Location AS City, COUNT(*) AS Claims
        FROM Claims c
        JOIN Food_Listings f ON f.Food_ID = c.Food_ID
        GROUP BY f.Location
        ORDER BY Claims DESC
        LIMIT 10;
    """,
    "Listings Near Expiry": f"""
        SELECT Food_ID, Food_Name, Quantity, Expiry_Date, Location
        FROM Food_Listings
        WHERE date(Expiry_Date) <= date('{today}', '+1 day')
        ORDER BY date(Expiry_Date) ASC;
    """,
    "Total Wasted Food": """
        SELECT COUNT(*) AS Wasted_Listings, SUM(Quantity) AS Wasted_Quantity
        FROM Food_Listings
        WHERE date(Expiry_Date) < date('now');
    """
}

for title, sql in queries.items():
    st.markdown(f"### {title}")
    try:
        df = run_sql(sql)
        st.dataframe(df)
    except Exception as e:
        st.warning(f"⚠️ Query failed: {e}")
