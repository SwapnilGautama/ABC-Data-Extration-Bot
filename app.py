import streamlit as st
import pandas as pd
import io
from datetime import datetime
import openai

# Load Excel from GitHub raw URL
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SwapnilGautama/ABC-Data-Extration-Bot/main/Customer_Master_Enhanced.xlsx"
    df = pd.read_excel(url)
    return df

# Function to filter based on user input
def filter_data(df, query):
    # Naive filter using simple keywords — extend as needed
    filtered = df.copy()

    if "product a" in query.lower():
        filtered = filtered[filtered['product'].str.lower() == 'product a']
    elif "product b" in query.lower():
        filtered = filtered[filtered['product'].str.lower() == 'product b']

    if "2025-05-24" in query:
        filtered = filtered[filtered['report_date'] == "2025-05-24"]

    return filtered

# Function to generate Excel from filtered data
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Data')
    processed_data = output.getvalue()
    return processed_data

# Load the data
df = load_data()

# Sidebar: Show available report dates and products
with st.sidebar:
    st.header("📅 Available Report Dates")
    report_dates = df['report_date'].dropna().unique()
    for date in sorted(report_dates):
        if isinstance(date, str):
            st.markdown(f"- {date}")
        else:
            st.markdown(f"- {date.strftime('%Y-%m-%d')}")

    st.header("📦 Available Products")
    products = df['product'].dropna().unique()
    for product in sorted(products):
        st.markdown(f"- {product}")

# Main UI
st.title("📊 Data Extraction Chatbot")

user_input = st.text_input("Ask a question about the dataset (e.g., 'Show Product A data for 2025-05-24')")

if user_input:
    st.write("Processing your request...")

    # Filter data based on the query
    filtered_df = filter_data(df, user_input)

    if not filtered_df.empty:
        st.success("Here is your extracted data:")
        st.dataframe(filtered_df)

        # Provide download link for Excel
        excel_data = to_excel(filtered_df)
        st.download_button(label="📥 Download Excel",
                           data=excel_data,
                           file_name='filtered_data.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.warning("No matching records found.")
