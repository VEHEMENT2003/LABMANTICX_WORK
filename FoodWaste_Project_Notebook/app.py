import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "food_app.db"

# Helper to run SQL
def run_sql(query, params=None):
    if params is None: params = {}
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(query, con, params=params)

# Helper to execute SQL (INSERT/UPDATE/DELETE)
def exec_sql(query, params=()):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(query, params)
        con.commit()

# ------------------ UI ------------------
st.set_page_config(page_title="🍲 Food Wastage Management", layout="wide")
st.title("🍲 Local Food Wastage Management System")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Food Listings", "Make a Claim", "Manage Providers"])

# ------------------ Dashboard ------------------
if menu == "Dashboard":
    st.subheader("📊 Dashboard Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        providers_count = run_sql("SELECT COUNT(*) as c FROM providers")["c"][0]
        st.metric("Providers", providers_count)

    with col2:
        receivers_count = run_sql("SELECT COUNT(*) as c FROM receivers")["c"][0]
        st.metric("Receivers", receivers_count)

    with col3:
        claims_count = run_sql("SELECT COUNT(*) as c FROM claims")["c"][0]
        st.metric("Claims", claims_count)

    st.markdown("---")

    st.write("### Food Listings by City")
    df = run_sql("SELECT location, COUNT(*) as cnt FROM food_listings GROUP BY location ORDER BY cnt DESC")
    if not df.empty:
        st.bar_chart(df.set_index("location"))

    st.write("### Claim Status Distribution")
    df2 = run_sql("SELECT status, COUNT(*) as cnt FROM claims GROUP BY status")
    if not df2.empty:
        st.dataframe(df2)
        st.write("Pie Chart not native — view in notebook.")


# ------------------ Food Listings ------------------
elif menu == "Food Listings":
    st.subheader("🥗 Available Food Listings")

    df = run_sql("SELECT * FROM food_listings WHERE IFNULL(is_expired,0)=0 ORDER BY expiry_date")
    if df.empty:
        st.warning("No active food listings available.")
    else:
        # Filters
        city = st.selectbox("Filter by City", ["All"] + sorted(df["location"].dropna().unique().tolist()))
        food_type = st.selectbox("Filter by Food Type", ["All"] + sorted(df["food_type"].dropna().unique().tolist()))

        filtered = df.copy()
        if city != "All":
            filtered = filtered[filtered["location"] == city]
        if food_type != "All":
            filtered = filtered[filtered["food_type"] == food_type]

        st.dataframe(filtered)


# ------------------ Make a Claim ------------------
elif menu == "Make a Claim":
    st.subheader("📥 Claim Food")

    food_df = run_sql("SELECT food_id, food_name, location, quantity FROM food_listings WHERE IFNULL(is_expired,0)=0")
    receiver_df = run_sql("SELECT receiver_id, name FROM receivers")

    if food_df.empty or receiver_df.empty:
        st.warning("No available food or receivers found.")
    else:
        food_choice = st.selectbox("Select Food", food_df["food_id"].astype(str) + " - " + food_df["food_name"])
        receiver_choice = st.selectbox("Select Receiver", receiver_df["receiver_id"].astype(str) + " - " + receiver_df["name"])
        claim_id = st.number_input("Claim ID", min_value=1, step=1)

        if st.button("Submit Claim"):
            food_id = int(food_choice.split(" - ")[0])
            receiver_id = int(receiver_choice.split(" - ")[0])
            exec_sql("INSERT INTO claims (claim_id, food_id, receiver_id, status) VALUES (?,?,?,?)",
                     (claim_id, food_id, receiver_id, "Pending"))
            st.success("✅ Claim submitted successfully!")


# ------------------ Manage Providers ------------------
elif menu == "Manage Providers":
    st.subheader("🏢 Manage Providers")

    st.write("### Add New Provider")
    provider_id = st.number_input("Provider ID", min_value=1, step=1)
    name = st.text_input("Name")
    type_ = st.text_input("Type")
    address = st.text_input("Address")
    city = st.text_input("City")
    contact = st.text_input("Contact")

    if st.button("Add Provider"):
        exec_sql("INSERT INTO providers (provider_id, name, type, address, city, contact) VALUES (?,?,?,?,?,?)",
                 (provider_id, name, type_, address, city, contact))
        st.success("✅ Provider added successfully!")

    st.markdown("---")

    st.write("### Existing Providers")
    df = run_sql("SELECT * FROM providers")
    st.dataframe(df)
