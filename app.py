import streamlit as st
import pandas as pd
import io
import openai
import dateparser
from datetime import datetime

# Load Excel from GitHub raw URL
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    df = pd.read_excel(url)
    return df

# Function to filter based on user input
def filter_data(df, query):
    filtered = df.copy()

    # Extract date using dateparser
    parsed_date = dateparser.parse(query)
    if parsed_date:
        parsed_date_str = parsed_date.strftime('%Y-%m-%d')
        filtered = filtered[filtered['report_date'].astype(str).str.startswith(parsed_date_str)]

    # Filter by product keyword
    products = df['product'].dropna().unique()
    for product in products:
        if product.lower() in query.lower():
            filtered = filtered[filtered['product'].str.lower() == product.lower()]
            break

    return filtered

# UI
st.set_page_config(page_title="ABC Data Extraction Bot", layout="wide")
st.title("🤖 Chat with ABC Data Extractor")

# Sidebar - show available filters
st.sidebar.markdown("### 🗓️ Available Report Dates")
df = load_data()
report_dates = sorted(df['report_date'].astype(str).unique())
for date in report_dates:
    st.sidebar.markdown(f"- {date}")

st.sidebar.markdown("### 📦 Available Products")
products = df['product'].dropna().unique()
for p in sorted(products):
    st.sidebar.markdown(f"- {p}")

# User input
user_input = st.text_input("Ask a question about the data (e.g., 'gold loan data for 24th May')")

if user_input:
    st.write("Processing your request...")
    filtered_df = filter_data(df, user_input)

    if not filtered_df.empty:
        st.success("Here is your extracted data:")
        st.dataframe(filtered_df)

        # Download link
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Extract')
        st.download_button("📥 Download Excel", output.getvalue(), file_name="filtered_data.xlsx")
    else:
        st.warning("No matching data found. Please try refining your query.")
