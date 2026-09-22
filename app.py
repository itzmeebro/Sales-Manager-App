import streamlit as st
import pandas as pd
from datetime import datetime

# გვერდის კონფიგურაცია
st.set_page_config(page_title="გაყიდვების მენეჯმენტი", layout="wide")

# სესიის მონაცემთა ბაზის ინიციალიზაცია (დემო მონაცემებით)
if 'orders' not in st.session_state:
    st.session_state.orders = pd.DataFrame([
        {
            "შეკვეთის #": 1001,
            "მომხმარებელი": "გიორგი ბერიძე",
            "ტელეფონი": "599123456",
            "მისამართი": "თბილისი, რუსთაველის გამზ. 12",
            "თარიღი": pd.to_datetime("2026-09-20").date(),
            "თვითღირებულება (₾)": 45.0,
            "გაყიდვის ფასი (₾)": 90.0,
            "მოგება (₾)": 45.0,
            "სტატუსი": "ჩაბარებულია",
            "გადახდის მეთოდი": "ბარათი"
        },
        {
            "შეკვეთის #": 1002,
            "მომხმარებელი": "ანა კაპანაძე",
            "ტელეფონი": "577987654",
            "მისამართი": "ბათუმი, გორგილაძის ქ. 45",
            "თარიღი": pd.to_datetime("2026-09-21").date(),
            "თვითღირებულება (₾)": 120.0,
            "გაყიდვის ფასი (₾)": 210.0,
            "მოგება (₾)": 90.0,
            "სტატუსი": "გზაშია",
            "გადახდის მეთოდი": "ნაღდი ანგარიშსწორება"
        }
    ])

st.title("📦 ონლაინ მაღაზიის გაყიდვების მენეჯმენტი")

# --- გვერდითა პანელი: ახალი შეკვეთის დამატება ---
st.sidebar.header("➕ ახალი შეკვეთის დამატება")
with st.sidebar.form("new_order_form", clear_on_submit=True):
    customer = st.text_input("მომხმარებლის სახელი, გვარი")
    phone = st.text_input("ტელეფონის ნომერი")
    address = st.text_area("მიწოდების მისამართი")
    order_date = st.date_input("თარიღი", datetime.now())
    
    cost_price = st.number_input("რეალური ფასი / თვითღირებულება (₾)", min_value=0.0, step=1.0)
    sale_price = st.number_input("გაყიდვის ფასი (₾)", min_value=0.0, step=1.0)
    
    payment_method = st.selectbox("გადახდის მეთოდი", ["ბარათი", "გადარიცხვა", "ნაღდი ანგარიშსწორება"])
    status = st.selectbox("სტატუსი", ["მუშავდება", "გზაშია", "ჩაბარებულია", "გაუქმებულია"])
    
    submitted = st.form_submit_button("შეკვეთის შენახვა")
    
    if submitted:
        if not customer or not phone:
            st.sidebar.error("გთხოვთ შეავსოთ სავალდებულო ველები (სახელი და ნომერი)!")
        else:
            # ახალი ID-ს გენერირება
            next_id = 1001 if st.session_state.orders.empty else st.session_state.orders["შეკვეთის #"].max() + 1
            profit = sale_price - cost_price
            
            new_row = {
                "შეკვეთის #": next_id,
                "მომხმარებელი": customer,
                "ტელეფონი": phone,
                "მისამართი": address,
                "თარიღი": order_date,
                "თვითღირებულება (₾)": cost_price,
                "გაყიდვის ფასი (₾)": sale_price,
                "მოგება (₾)": profit,
                "სტატუსი": status,
                "გადახდის მეთოდი": payment_method
            }
            
            st.session_state.orders = pd.concat([st.session_state.orders, pd.DataFrame([new_row])], ignore_index=True)
            st.sidebar.success(f"შეკვეთა #{next_id} წარმატებით დაემატა!")

# --- ფილტრების სექცია ---
st.subheader("🔍 ფილტრაცია და ძებნა")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    search_query = st.text_input("🔎 ძებნა (სახელი / ნომერი / #)")
with col_f2:
    status_filter = st.multiselect("სტატუსი", options=["მუშავდება", "გზაშია", "ჩაბარებულია", "გაუქმებულია"])
with col_f3:
    min_price, max_price = st.slider("გაყიდვის ფასის დიაპაზონი (₾)", 0, 2000, (0, 2000))
with col_f4:
    date_range = st.date_input("თარიღების დიაპაზონი", [])

# ფილტრაციის ლოგიკა
filtered_df = st.session_state.orders.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df["მომხმარებელი"].astype(str).str.contains(search_query, case=False) |
        filtered_df["ტელეფონი"].astype(str).str.contains(search_query) |
        filtered_df["შეკვეთის #"].astype(str).str.contains(search_query)
    ]

if status_filter:
    filtered_df = filtered_df[filtered_df["სტატუსი"].isin(status_filter)]

filtered_df = filtered_df[
    (filtered_df["გაყიდვის ფასი (₾)"] >= min_price) & 
    (filtered_df["გაყიდვის ფასი (₾)"] <= max_price)
]

if len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[
        (filtered_df["თარიღი"] >= start_d) & 
        (filtered_df["თარიღი"] <= end_d)
    ]

# --- ანალიტიკური ბარათები (KPIs) ---
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
total_sales = filtered_df["გაყიდვის ფასი (₾)"].sum()
total_cost = filtered_df["თვითღირებულება (₾)"].sum()
total_profit = filtered_df["მოგება (₾)"].sum()
total_orders = len(filtered_df)

m1.metric("სულ შეკვეთები", f"{total_orders} ცალი")
m2.metric("სულ შემოსავალი", f"{total_sales:,.2f} ₾")
m3.metric("სულ თვითღირებულება", f"{total_cost:,.2f} ₾")
m4.metric("სუფთა მოგება", f"{total_profit:,.2f} ₾")
st.markdown("---")

# --- ცხრილის ჩვენება და რედაქტირება ---
st.subheader("📋 შეკვეთების სრული სია")
st.caption("შეგიძლიათ პირდაპირ ცხრილში შეცვალოთ მონაცემები (მაგ. შეცვალოთ სტატუსი ან ფასი).")

edited_df = st.data_editor(
    filtered_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "სტატუსი": st.column_config.SelectboxColumn(
            "სტატუსი",
            options=["მუშავდება", "გზაშია", "ჩაბარებულია", "გაუქმებულია"],
            required=True
        ),
        "გადახდის მეთოდი": st.column_config.SelectboxColumn(
            "გადახდის მეთოდი",
            options=["ბარათი", "გადარიცხვა", "ნაღდი ანგარიშსწორება"]
        ),
        "გაყიდვის ფასი (₾)": st.column_config.NumberColumn(format="%.2f ₾"),
        "თვითღირებულება (₾)": st.column_config.NumberColumn(format="%.2f ₾"),
        "მოგება (₾)": st.column_config.NumberColumn(format="%.2f ₾"),
    }
)

# მონაცემების ექსპორტი
st.download_button(
    label="📥 Excel/CSV ფაილად ჩამოტვირთვა",
    data=filtered_df.to_csv(index=False).encode('utf-8-sig'),
    file_name=f"orders_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
