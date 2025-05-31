import streamlit as st
import pandas as pd
import openai
import io
import requests
from datetime import datetime, date
import matplotlib.pyplot as plt

# Set Streamlit page config
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

    df.columns = df.columns.str.strip()

    if 'report_date' in df.columns:
        df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')

    if 'DOB' in df.columns:
        df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')

    return df

# Filter logic
def filter_data(df, query):
    filtered = df.copy()
    query = query.lower()

    # Product
    if 'product' in df:
        matched_product = None
        for prod in df['product'].dropna().unique():
            if prod.lower() in query:
                matched_product = prod
                break
        if matched_product:
            filtered = filtered[filtered['product'].str.lower() == matched_product.lower()]

    # KYC
    if 'KYC_Verified' in df:
        if any(term in query for term in ["kyc no", "kyc not verified", "not kyc verified", "not verified"]):
            filtered = filtered[filtered['KYC_Verified'].astype(str).str.upper() == 'N']
        elif any(term in query for term in ["kyc yes", "kyc verified", "verified kyc"]):
            filtered = filtered[filtered['KYC_Verified'].astype(str).str.upper() == 'Y']

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

# Sidebar filters
def sidebar_filters(df):
    st.sidebar.markdown("### 📅 Available Report Dates")
    if 'report_date' in df:
        for date in sorted(df['report_date'].dropna().dt.strftime('%Y-%m-%d').unique()):
            st.sidebar.markdown(f"- {date}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📦 Available Products")
    if 'product' in df:
        for product in sorted(df['product'].dropna().unique()):
            st.sidebar.markdown(f"- {product}")

# Chart utilities
def plot_pie_chart(series, title, slot):
    fig, ax = plt.subplots()
    series.value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
    ax.set_ylabel("")
    ax.set_title(title)
    slot.pyplot(fig)

def plot_bar_chart(series, title, slot):
    fig, ax = plt.subplots()
    series.value_counts().sort_values().plot.barh(ax=ax)
    ax.set_title(title)
    slot.pyplot(fig)

def plot_line_chart(series, title, slot):
    fig, ax = plt.subplots()
    formatted = series.dropna().dt.strftime('%Y-%m-%d')
    formatted.value_counts().sort_index().plot(ax=ax, kind='line', marker='o')
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")
    ax.grid(True)
    slot.pyplot(fig)

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

        # ------------------ INSIGHTS SECTION ------------------
        st.markdown("### 📊 Insights on Filtered Data")

        col1, col2, col3 = st.columns(3)
        if 'KYC_Verified' in result:
            plot_pie_chart(result['KYC_Verified'], "KYC Verification Status", col1)

        if 'product' in result:
            plot_bar_chart(result['product'], "Product Distribution", col2)

        if 'report_date' in result:
            plot_line_chart(result['report_date'], "Report Date Distribution", col3)

        col4, col5, col6 = st.columns(3)
        if 'Employment_Type' in result:
            plot_bar_chart(result['Employment_Type'], "Employment Type Distribution", col4)

        if 'DOB' in result:
            today = date.today()
            dob_series = result['DOB'].dropna()
            age_bucket = pd.cut(
                dob_series.apply(lambda dob: today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))),
                bins=[0, 30, 40, 50, 60, 150],
                labels=["Under 30", "30-40", "40-50", "50-60", "60+"],
                right=False
            )
            if not age_bucket.empty:
                plot_pie_chart(age_bucket, "Age Distribution", col5)

        # ------------------------------------------------------

        st.dataframe(result)

        # Excel download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name='FilteredData')
        st.download_button("⬇️ Download Excel", output.getvalue(), file_name="filtered_data.xlsx", mime="application/vnd.ms-excel")

    else:
        st.warning("No results found for your query. Please try refining it.")
