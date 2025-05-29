import streamlit as st
import pandas as pd
import openai
import io
import requests
from datetime import datetime

# Set Streamlit page config first
st.set_page_config(page_title="ABC Data Extractor", page_icon="📘")

# Load Excel from GitHub
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"Failed to load data. HTTP {response.status_code}")
        return pd.DataFrame()  # return empty DataFrame to prevent crash

    # Read Excel from bytes
    excel_file = io.BytesIO(response.content)
    df = pd.read_excel(excel_file)
    return df
    
# Clean and match text
def normalize(text):
    return str(text).strip().lower()

# Filter function using user query
def filter_data(df, query):
    filtered = df.copy()
    q = normalize(query)

    # Filter by product
    products = df['product'].dropna().unique()
    matched_products = [p for p in products if normalize(p) in q]
    if matched_products:
        filtered = filtered[filtered['product'].isin(matched_products)]

    # Filter by date
    dates = df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()
    matched_dates = [d for d in dates if d in q or datetime.strptime(d, "%Y-%m-%d").strftime("%d %B").lower() in q or datetime.strptime(d, "%Y-%m-%d").strftime("%d %b").lower() in q]
    if matched_dates:
        filtered = filtered[filtered['report_date'].dt.strftime('%Y-%m-%d').isin(matched_dates)]

    return filtered

# Sidebar display for user clarity
def sidebar_filters(df):
    st.sidebar.markdown("### 📅 Available Report Dates")
    for date in sorted(df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()):
        st.sidebar.markdown(f"- {date}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📦 Available Products")
    for product in sorted(df['product'].dropna().unique()):
        st.sidebar.markdown(f"- {product}")

# App UI
st.title("📘 Chat with ABC Data Extractor")
user_input = st.text_input("Ask a question about the data (e.g. 'show me gold loan data from 24th May')")

df = load_data()
sidebar_filters(df)

if user_input:
    st.markdown("Processing your request...")

    result = filter_data(df, user_input)

    if not result.empty:
        st.success("Here is your extracted data:")
        st.markdown(f"🔹 **{len(result)} rows** matched your query.")
        st.dataframe(result)

        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name='FilteredData')
        st.download_button("⬇️ Download Excel", output.getvalue(), file_name="filtered_data.xlsx", mime="application/vnd.ms-excel")

    else:
        st.warning("No results found for your query. Please try refining it.")
