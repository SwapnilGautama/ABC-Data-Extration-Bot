import streamlit as st
import pandas as pd
import openai
import io
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil import parser
import re

# Set Streamlit page config first
st.set_page_config(page_title="ABC Data Extractor", page_icon="📘")

# Load Excel from GitHub
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"Failed to load data. HTTP {response.status_code}")
        return pd.DataFrame()

    excel_file = io.BytesIO(response.content)
    df = pd.read_excel(excel_file)
    
    # Ensure 'report_date' is datetime
    df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')
    return df

# Filter logic
def filter_data(df, query):
    filtered = df.copy()
    query = query.lower()

    # Product filter
    for prod in df['product'].dropna().unique():
        if prod.lower() in query:
            filtered = filtered[filtered['product'].str.lower() == prod.lower()]
            break

    # KYC filter
    if "kyc verified" in query or "kyc yes" in query:
        filtered = filtered[filtered['kyc_verified'].astype(str).str.lower() == "yes"]
    elif "kyc not verified" in query or "kyc no" in query:
        filtered = filtered[filtered['kyc_verified'].astype(str).str.lower() == "no"]

    # Employment type filter
    for emp_type in df['employment_type'].dropna().unique():
        if emp_type.lower() in query:
            filtered = filtered[filtered['employment_type'].str.lower() == emp_type.lower()]
            break

    # City filter
    for city in df['city'].dropna().unique():
        if city.lower() in query:
            filtered = filtered[filtered['city'].str.lower() == city.lower()]
            break

    # State filter
    for state in df['state'].dropna().unique():
        if state.lower() in query:
            filtered = filtered[filtered['state'].str.lower() == state.lower()]
            break

    # Date filter
    date_match = re.search(r'\d{1,2}[a-z]{0,2}\s+[A-Za-z]+|\d{4}-\d{2}-\d{2}', query)
    if date_match:
        try:
            parsed_date = parser.parse(date_match.group()).date()
            filtered = filtered[filtered['report_date'].dt.date == parsed_date]
        except:
            pass

    return filtered

# Sidebar: Display report dates and products
def sidebar_filters(df):
    st.sidebar.markdown("### 📅 Available Report Dates")
    for date in sorted(df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()):
        st.sidebar.markdown(f"- {date}")

    st.sidebar.markdown("### 📦 Available Products")
    for product in sorted(df['product'].dropna().unique()):
        st.sidebar.markdown(f"- {product}")

    st.sidebar.markdown("### 👤 Employment Types")
    for emp in sorted(df['employment_type'].dropna().unique()):
        st.sidebar.markdown(f"- {emp}")

    st.sidebar.markdown("### 🏙️ Cities")
    for city in sorted(df['city'].dropna().unique()):
        st.sidebar.markdown(f"- {city}")

    st.sidebar.markdown("### 🗺️ States")
    for state in sorted(df['state'].dropna().unique()):
        st.sidebar.markdown(f"- {state}")

# Chart rendering utility
def plot_pie_chart(data, title):
    fig, ax = plt.subplots()
    data.value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
    ax.set_ylabel("")
    ax.set_title(title)
    st.pyplot(fig)

# Main app
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

        # Download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name='FilteredData')
        st.download_button("⬇️ Download Excel", output.getvalue(), file_name="filtered_data.xlsx", mime="application/vnd.ms-excel")

        # Insights
        st.markdown("### 📊 Insights on Filtered Data")
        try:
            kyc_yes_pct = (result['kyc_verified'].str.lower() == 'yes').sum() / len(result) * 100
            st.markdown(f"- ✅ **{kyc_yes_pct:.1f}%** of filtered records are KYC verified.")
        except:
            st.warning("Couldn't compute KYC stats.")

        if 'product' in result:
            plot_pie_chart(result['product'], "Product Distribution")
        if 'report_date' in result:
            plot_pie_chart(result['report_date'].dt.strftime('%Y-%m-%d'), "Report Date Breakdown")
        if 'employment_type' in result:
            plot_pie_chart(result['employment_type'], "Employment Type Breakdown")

    else:
        st.warning("No results found for your query. Please try refining it.")
