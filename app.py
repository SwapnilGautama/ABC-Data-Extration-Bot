import streamlit as st
import pandas as pd
import io
import openai
from datetime import datetime

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
    if "last 3 days" in query.lower():
        today = df['report_date'].max()
        last_3 = today - pd.Timedelta(days=3)
        filtered = filtered[filtered['report_date'] >= last_3]
    
    return filtered

# Streamlit UI
st.title("📊 ABC Data Extraction Chatbot")

st.markdown("Ask a question about the data, e.g.: `Show me data for Product A from last 3 days`")

user_input = st.text_input("Your query")

if user_input:
    df = load_data()
    result_df = filter_data(df, user_input)

    st.write(f"🔍 Showing {len(result_df)} records based on your query")

    st.dataframe(result_df.head(20))

    # Create downloadable Excel
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        result_df.to_excel(writer, index=False, sheet_name='Filtered')
    towrite.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=towrite,
        file_name="filtered_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
