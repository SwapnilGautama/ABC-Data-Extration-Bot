import streamlit as st
import pandas as pd
import io
import openai
import requests
from datetime import datetime

# Load Excel from GitHub raw URL using requests
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to download Excel file from GitHub.")
    
    excel_file = io.BytesIO(response.content)
    df = pd.read_excel(excel_file)
    return df

# Function to filter based on user input
def filter_data(df, query):
    filtered = df.copy()

    if "product" in query.lower():
        for prod in df['product'].unique():
            if prod.lower() in query.lower():
                filtered = filtered[filtered['product'].str.lower() == prod.lower()]
                break

    if "report_date" in query.lower() or "may" in query.lower():
        for date in df['report_date'].dt.date.unique():
            date_str = date.strftime("%Y-%m-%d")
            if date_str in query or date.strftime("%d") in query:
                filtered = filtered[filtered['report_date'].dt.date == date]
                break

    return filtered

# Function to handle user input and generate response
def user_input(query, df):
    filtered_df = filter_data(df, query)

    if filtered_df.empty:
        return None, "Sorry, no records matched your query."
    
    output = io.BytesIO()
    filtered_df.to_excel(output, index=False, engine='xlsxwriter')
    output.seek(0)
    
    return output, "Here is your extracted data:"

# Load the data
df = load_data()

# UI Design
st.set_page_config(page_title="ABC Data Extractor", page_icon="📚")
st.title("📚 Chat with ABC Data Extractor")

# Sidebar with available report dates and products
with st.sidebar:
    st.markdown("### 📅 Available Report Dates")
    for date in sorted(df['report_date'].dt.date.unique()):
        st.write(f"- {date}")

    st.markdown("---")
    st.markdown("### 📦 Available Products")
    for product in sorted(df['product'].unique()):
        st.write(f"- {product}")

# User Input
query = st.text_input("Ask a question about the data:", placeholder="e.g. Show me gold loan records for 24th May")

if query:
    st.write("Processing your request...")
    output, message = user_input(query, df)

    if output:
        st.success(message)
        st.dataframe(pd.read_excel(output))
        st.download_button("📥 Download Excel", data=output, file_name="filtered_data.xlsx")
    else:
        st.warning(message)
