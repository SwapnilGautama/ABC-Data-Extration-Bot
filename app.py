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

    # Strip column names
    df.columns = df.columns.str.strip()

    # Convert report_date
    if 'report_date' in df.columns:
        df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')

    return df

# Clean and match text
def filter_data(df, query):
    filtered = df.copy()
    query = query.lower()

    # Product
    if 'product' in df:
        for prod in df['product'].dropna().unique():
            if prod.lower() in query:
                filtered = filtered[filtered['product'].str.lower() == prod.lower()]
                break

    # KYC Verified
    if 'KYC_Verified' in df:
        if "kyc yes" in query or "kyc verified" in query:
            filtered = filtered[filtered['KYC_Verified'].astype(str).str.upper() == "Y"]
        elif "kyc no" in query or "kyc not verified" in query:
            filtered = filtered[filtered['KYC_Verified'].astype(str).str.upper() == "N"]

    # Employment Type
    if 'Employment_Type' in df:
        for emp in df['Employment_Type'].dropna().unique():
            if emp.lower() in query:
                filtered = filtered[filtered['Employment_Type'].str.lower() == emp.lower()]
                break

    # City
    if 'City' in df:
        for city in df['City'].dropna().unique():
            if city.lower() in query:
                filtered = filtered[filtered['City'].str.lower() == city.lower()]
                break

    # State
    if 'State' in df:
        for state in df['State'].dropna().unique():
            if state.lower() in query:
                filtered = filtered[filtered['State'].str.lower() == state.lower()]
                break

    # Date
    from dateutil import parser
    import re
    if 'report_date' in df:
        date_match = re.search(r'\d{1,2}[a-z]{0,2}\s+[A-Za-z]+|\d{4}-\d{2}-\d{2}', query)
        if date_match:
            try:
                parsed_date = parser.parse(date_match.group()).date()
                filtered = filtered[filtered['report_date'].dt.date == parsed_date]
            except:
                pass

    return filtered

# Sidebar display
def sidebar_filters(df):
    if 'report_date' in df:
        st.sidebar.markdown("### 📅 Available Report Dates")
        for date in sorted(df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()):
            st.sidebar.markdown(f"- {date}")

    if 'product' in df:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📦 Available Products")
        for product in sorted(df['product'].dropna().unique()):
            st.sidebar.markdown(f"- {product}")

    if 'Employment_Type' in df:
        st.sidebar.markdown("### 👤 Employment Types")
        for emp in sorted(df['Employment_Type'].dropna().unique()):
            st.sidebar.markdown(f"- {emp}")

    if 'KYC_Verified' in df:
        st.sidebar.markdown("### ✅ KYC Verified")
        for kyc in sorted(df['KYC_Verified'].dropna().unique()):
            st.sidebar.markdown(f"- {kyc}")

    if 'City' in df:
        st.sidebar.markdown("### 🏙️ Cities")
        for city in sorted(df['City'].dropna().unique()):
            st.sidebar.markdown(f"- {city}")

    if 'State' in df:
        st.sidebar.markdown("### 🗺️ States")
        for state in sorted(df['State'].dropna().unique()):
            st.sidebar.markdown(f"- {state}")

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
