import streamlit as st
import pandas as pd
import io
import requests
from datetime import datetime
from dateutil import parser
import re
import matplotlib.pyplot as plt

# Set Streamlit page config
st.set_page_config(page_title="ABC Data Extractor", page_icon="📘")

# Load data with error handling
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.error(f"Failed to load data. HTTP {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()

    df = pd.read_excel(io.BytesIO(response.content))
    df.columns = df.columns.str.strip().str.lower()

    if 'report_date' in df.columns:
        df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')

    return df

# Filter logic
def filter_data(df, query):
    filtered = df.copy()
    query = query.lower()

    if 'product' in df:
        for prod in df['product'].dropna().unique():
            if prod.lower() in query:
                filtered = filtered[filtered['product'].str.lower() == prod.lower()]
                break

    if 'kyc_verified' in df:
        if "kyc yes" in query or "kyc verified" in query:
            filtered = filtered[filtered['kyc_verified'].str.upper() == "Y"]
        elif "kyc no" in query or "kyc not verified" in query:
            filtered = filtered[filtered['kyc_verified'].str.upper() == "N"]

    if 'employment_type' in df:
        for emp in df['employment_type'].dropna().unique():
            if emp.lower() in query:
                filtered = filtered[filtered['employment_type'].str.lower() == emp.lower()]
                break

    if 'city' in df:
        for city in df['city'].dropna().unique():
            if city.lower() in query:
                filtered = filtered[filtered['city'].str.lower() == city.lower()]
                break

    if 'state' in df:
        for state in df['state'].dropna().unique():
            if state.lower() in query:
                filtered = filtered[filtered['state'].str.lower() == state.lower()]
                break

    if 'report_date' in df:
        date_match = re.search(r'\d{1,2}[a-z]{0,2}\s+[A-Za-z]+|\d{4}-\d{2}-\d{2}', query)
        if date_match:
            try:
                parsed_date = parser.parse(date_match.group()).date()
                filtered = filtered[filtered['report_date'].dt.date == parsed_date]
            except:
                pass

    return filtered

# Sidebar filters
def sidebar_filters(df):
    if 'report_date' in df:
        st.sidebar.markdown("### 📅 Available Report Dates")
        for date in sorted(df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()):
            st.sidebar.markdown(f"- {date}")

    if 'product' in df:
        st.sidebar.markdown("### 📦 Available Products")
        for prod in sorted(df['product'].dropna().unique()):
            st.sidebar.markdown(f"- {prod}")

    if 'employment_type' in df:
        st.sidebar.markdown("### 👤 Employment Types")
        for emp in sorted(df['employment_type'].dropna().unique()):
            st.sidebar.markdown(f"- {emp}")

    if 'city' in df:
        st.sidebar.markdown("### 🏙️ Cities")
        for city in sorted(df['city'].dropna().unique()):
            st.sidebar.markdown(f"- {city}")

    if 'state' in df:
        st.sidebar.markdown("### 🗺️ States")
        for state in sorted(df['state'].dropna().unique()):
            st.sidebar.markdown(f"- {state}")

# Pie chart
def plot_pie_chart(data, title):
    fig, ax = plt.subplots()
    data.value_counts().nlargest(10).plot.pie(autopct='%1.1f%%', ax=ax)
    ax.set_ylabel("")
    ax.set_title(title)
    st.pyplot(fig)

# Main App
st.title("📘 Chat with ABC Data Extractor")
df = load_data()

if not df.empty:
    sidebar_filters(df)

    with st.form("query_form"):
        user_input = st.text_input("Ask a question about the data (e.g. 'show me gold loan data from 24th May')", "")
        submitted = st.form_submit_button("Submit")

    if submitted and user_input.strip():
        with st.spinner("Processing your request..."):
            result = filter_data(df, user_input)

            if not result.empty:
                st.success("Here is your extracted data:")
                st.markdown(f"🔹 **{len(result)} rows** matched your query.")
                st.dataframe(result)

                # Excel export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result.to_excel(writer, index=False, sheet_name='FilteredData')
                st.download_button("⬇️ Download Excel", output.getvalue(), file_name="filtered_data.xlsx", mime="application/vnd.ms-excel")

                # Charts
                st.markdown("### 📊 Insights on Filtered Data")
                if 'kyc_verified' in result:
                    try:
                        pct = (result['kyc_verified'].str.upper() == 'Y').sum() / len(result) * 100
                        st.markdown(f"- ✅ **{pct:.1f}%** are KYC Verified")
                    except:
                        pass

                if 'product' in result:
                    plot_pie_chart(result['product'], "Product Distribution")
                if 'report_date' in result:
                    plot_pie_chart(result['report_date'].dt.strftime('%Y-%m-%d'), "Report Date Distribution")
                if 'employment_type' in result:
                    plot_pie_chart(result['employment_type'], "Employment Type Breakdown")
                if 'kyc_verified' in result:
                    plot_pie_chart(result['kyc_verified'], "KYC Status Breakdown")
            else:
                st.warning("No results found for your query. Please refine and try again.")
