# food.py
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

def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Providers (
            Provider_ID INTEGER PRIMARY KEY,
            Name TEXT,
            Provider_Type TEXT,
            Contact TEXT,
            City TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Receivers (
            Receiver_ID INTEGER PRIMARY KEY,
            Name TEXT,
            Contact TEXT,
            City TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Food_Listings (
            Food_ID INTEGER PRIMARY KEY,
            Food_Name TEXT,
            Food_Type TEXT,
            Meal_Type TEXT,
            Quantity INTEGER,
            Expiry_Date TEXT,
            Provider_ID INTEGER,
            Location TEXT,
            FOREIGN KEY (Provider_ID) REFERENCES Providers (Provider_ID)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Claims (
            Claim_ID INTEGER PRIMARY KEY,
            Food_ID INTEGER,
            Receiver_ID INTEGER,
            Status TEXT,
            FOREIGN KEY (Food_ID) REFERENCES Food_Listings (Food_ID),
            FOREIGN KEY (Receiver_ID) REFERENCES Receivers (Receiver_ID)
        );
    """)
    conn.commit()

    # Insert sample data if empty
    cursor.execute("SELECT COUNT(*) FROM Providers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO Providers VALUES (?,?,?,?,?)", [
            (1, "FoodBank Hyderabad", "NGO", "9999999999", "Hyderabad"),
            (2, "FreshMart", "Supermarket", "8888888888", "Mumbai")
        ])
        cursor.executemany("INSERT INTO Receivers VALUES (?,?,?,?)", [
            (1, "Helping Hands", "7777777777", "Hyderabad"),
            (2, "City Shelter", "6666666666", "Mumbai")
        ])
        cursor.executemany("INSERT INTO Food_Listings VALUES (?,?,?,?,?,?,?,?)", [
            (1, "Rice Bags", "Grain", "Lunch", 100, "2025-08-20", 1, "Hyderabad"),
            (2, "Bread Packets", "Bakery", "Breakfast", 50, "2025-08-18", 2, "Mumbai")
        ])
        cursor.executemany("INSERT INTO Claims VALUES (?,?,?,?)", [
            (1, 1, 1, "Completed"),
            (2, 2, 2, "Pending")
        ])
        conn.commit()

init_db()

# Helper to run queries
def run_sql(q, params=None):
    return pd.read_sql_query(q, conn, params=params)

today = date.today().strftime('%Y-%m-%d')

# ========================
# 🌐 Streamlit App UI
# ========================
st.set_page_config(page_title="🍽️ Food Donation Management", layout="wide")
st.title("🍽️ Food Donation Management System")

# ------------------------------
# 🔍 FILTERS
# ------------------------------
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

st.subheader("📦 Filtered Food Listings")
try:
    filtered = run_sql(query, params)
    st.dataframe(filtered)
    if not filtered.empty:
        st.download_button("⬇️ Download CSV", filtered.to_csv(index=False), "filtered_food.csv", "text/csv")
except Exception as e:
    st.warning(f"⚠️ {e}")

# ------------------------------
# 📞 Contact Providers/Receivers
# ------------------------------
st.subheader("📞 Contact Directory")

tab1, tab2 = st.tabs(["Providers", "Receivers"])

with tab1:
    provs = run_sql("SELECT Provider_ID, Name, Provider_Type, Contact, City FROM Providers")
    st.dataframe(provs)
    st.download_button("⬇️ Download Providers", provs.to_csv(index=False), "providers.csv", "text/csv")

with tab2:
    recvs = run_sql("SELECT Receiver_ID, Name, Contact, City FROM Receivers")
    st.dataframe(recvs)
    st.download_button("⬇️ Download Receivers", recvs.to_csv(index=False), "receivers.csv", "text/csv")

# ------------------------------
# ✏️ CRUD OPERATIONS
# ------------------------------
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
    data = run_sql("SELECT * FROM Food_Listings LIMIT 20")
    st.dataframe(data)
    if not data.empty:
        st.download_button("⬇️ Download Food Listings", data.to_csv(index=False), "food_listings.csv", "text/csv")

# ------------------------------
# 📊 ALL 15+ QUERIES
# ------------------------------
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
        if not df.empty:
            st.download_button(f"⬇️ Download {title}", df.to_csv(index=False), f"{title}.csv", "text/csv")
    except Exception as e:
        st.warning(f"⚠️ Query failed: {e}")
