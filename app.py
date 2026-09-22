import streamlit as st
import pandas as pd
from datetime import datetime

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- მონაცემთა ბაზის ინიციალიზაცია ---
conn = sqlite3.connect('store_data.db', check_same_thread=False)
c = conn.cursor()

# users ცხრილი (დაემატა email)
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT
    )
''')

# orders ცხრილი
c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        customer TEXT,
        phone TEXT,
        address TEXT,
        order_date TEXT,
        cost_price REAL,
        sale_price REAL,
        profit REAL,
        status TEXT,
        payment_method TEXT
    )
''')
conn.commit()

# პაროლის დაჰეშვა
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# გვერდის კონფიგურაცია
st.set_page_config(page_title="გაყიდვების მენეჯმენტი", layout="wide")

# სესიის მდგომარეობა
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- ავტორიზაცია / რეგისტრაცია ---
if not st.session_state.logged_in:
    st.title("🔐 ავტორიზაცია / რეგისტრაცია")
    
    menu = ["შესვლა", "რეგისტრაცია"]
    choice = st.sidebar.selectbox("მენიუ", menu)
    
    if choice == "შესვლა":
        st.subheader("🔑 სისტემაში შესვლა")
        login_input = st.text_input("მომხმარებლის სახელი ან ელფოსტა")
        password = st.text_input("პაროლი", type='password')
        
        if st.button("შესვლა"):
            hashed_pswd = make_hashes(password)
            # ძებნა სახელით ან ელფოსტით
            c.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?', (login_input, login_input, hashed_pswd))
            result = c.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.username = result[0]  # username
                st.success(f"მოგესალმებით, {result[0]}!")
                st.rerun()
            else:
                st.error("არასწორი მონაცემები ან პაროლი")

    elif choice == "რეგისტრაცია":
        st.subheader("📝 ახალი ანგარიშის შექმნა")
        new_user = st.text_input("მომხმარებლის სახელი")
        new_email = st.text_input("ელფოსტა (Email)")
        new_password = st.text_input("პაროლი", type='password')
        
        if st.button("რეგისტრაცია"):
            if new_user and new_email and new_password:
                # შემოწმება, ხომ არ არსებობს ასეთი სახელი ან მეილი
                c.execute('SELECT * FROM users WHERE username = ? OR email = ?', (new_user, new_email))
                if c.fetchone():
                    st.warning("ასეთი მომხმარებელი ან ელფოსტა უკვე დარეგისტრირებულია!")
                else:
                    c.execute('INSERT INTO users(username, email, password) VALUES (?,?,?)', (new_user, new_email, make_hashes(new_password)))
                    conn.commit()
                    st.success("ანგარიში წარმატებით შეიქმნა! გადადით შესვლის გვერდზე.")
            else:
                st.error("გთხოვთ შეავსოთ ყველა ველი!")

# --- ძირითადი აპლიკაცია (შესვლის შემდეგ) ---
else:
    st.sidebar.write(f"👤 მომხმარებელი: **{st.session_state.username}**")
    if st.sidebar.button("გამოსვლა (Logout)"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("📦 გაყიდვების მენეჯმენტი")

    # --- ახალი შეკვეთის დამატება ---
    st.sidebar.header("➕ ახალი შეკვეთა")
    with st.sidebar.form("new_order_form", clear_on_submit=True):
        customer = st.text_input("მომხმარებლის სახელი")
        phone = st.text_input("ტელეფონის ნომერი")
        address = st.text_area("მისამართი")
        order_date = st.date_input("თარიღი", datetime.now())
        
        cost_price = st.number_input("თვითღირებულება (₾)", min_value=0.0, step=1.0)
        sale_price = st.number_input("გაყიდვის ფასი (₾)", min_value=0.0, step=1.0)
        
        payment_method = st.selectbox("გადახდა", ["ბარათი", "გადარიცხვა", "ნაღდი ანგარიშსწორება"])
        status = st.selectbox("სტატუსი", ["მუშავდება", "გზაშია", "ჩაბარებულია", "გაუქმებულია"])
        
        submitted = st.form_submit_button("შენახვა")
        
        if submitted:
            if not customer or not phone:
                st.sidebar.error("შეავსეთ სავალდებულო ველები!")
            else:
                profit = sale_price - cost_price
                c.execute('''
                    INSERT INTO orders (username, customer, phone, address, order_date, cost_price, sale_price, profit, status, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state.username, customer, phone, address, str(order_date), cost_price, sale_price, profit, status, payment_method))
                conn.commit()
                st.sidebar.success("შეკვეთა შენახულია!")
                st.rerun()

    # --- მხოლოდ მიმდინარე მომხმარებლის შეკვეთები ---
    df = pd.read_sql_query('SELECT id AS "შეკვეთის #", customer AS "მომხმარებელი", phone AS "ტელეფონი", address AS "მისამართი", order_date AS "თარიღი", cost_price AS "თვითღირებულება (₾)", sale_price AS "გაყიდვის ფასი (₾)", profit AS "მოგება (₾)", status AS "სტატუსი", payment_method AS "გადახდის მეთოდი" FROM orders WHERE username = ?', conn, params=(st.session_state.username,))

    # --- ფილტრები ---
    st.subheader("🔍 ფილტრაცია და ძებნა")
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        search_query = st.text_input("🔎 ძებნა (სახელი / ნომერი / #)")
    with col_f2:
        status_filter = st.multiselect("სტატუსი", options=["მუშავდება", "გზაშია", "ჩაბარებულია", "გაუქმებულია"])
    with col_f3:
        min_price, max_price = st.slider("გაყიდვის ფასის დიაპაზონი (₾)", 0, 2000, (0, 2000))

    filtered_df = df.copy()

    if search_query and not filtered_df.empty:
        filtered_df = filtered_df[
            filtered_df["მომხმარებელი"].astype(str).str.contains(search_query, case=False) |
            filtered_df["ტელეფონი"].astype(str).str.contains(search_query) |
            filtered_df["შეკვეთის #"].astype(str).str.contains(search_query)
        ]

    if status_filter and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["სტატუსი"].isin(status_filter)]

    if not filtered_df.empty:
        filtered_df = filtered_df[
            (filtered_df["გაყიდვის ფასი (₾)"] >= min_price) & 
            (filtered_df["გაყიდვის ფასი (₾)"] <= max_price)
        ]

    # --- KPIs ---
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    total_sales = filtered_df["გაყიდვის ფასი (₾)"].sum() if not filtered_df.empty else 0
    total_cost = filtered_df["თვითღირებულება (₾)"].sum() if not filtered_df.empty else 0
    total_profit = filtered_df["მოგება (₾)"].sum() if not filtered_df.empty else 0
    total_orders = len(filtered_df)

    m1.metric("სულ შეკვეთები", f"{total_orders} ცალი")
    m2.metric("სულ შემოსავალი", f"{total_sales:,.2f} ₾")
    m3.metric("სულ თვითღირებულება", f"{total_cost:,.2f} ₾")
    m4.metric("სუფთა მოგება", f"{total_profit:,.2f} ₾")
    st.markdown("---")

    # --- ცხრილი ---
    st.subheader("📋 ჩემი შეკვეთები")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
        
        st.download_button(
            label="📥 CSV ფაილად ჩამოტვირთვა",
            data=filtered_df.to_csv(index=False).encode('utf-8-sig'),
            file_name=f"my_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("შეკვეთები ჯერ არ არის დამატებული.")
