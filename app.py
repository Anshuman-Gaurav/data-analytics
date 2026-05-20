import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- Dashboard Configuration ---
st.set_page_config(page_title="APL Logistics Dashboard", layout="wide")
st.title("📦 APL Logistics Financial Dashboard")
st.markdown("An interactive overview of profitability, category performance, and discount impacts.")

# --- 1. Data Loading & Cleaning (Cached) ---
# @st.cache_data ensures the dashboard doesn't re-read and re-clean the CSV on every click
@st.cache_data
def load_and_clean_data():
    # Load Data
    df = pd.read_csv('APL_Logistics.csv', encoding='latin1')
    
    # Financial Validation & Currency Normalization
    financial_cols = [
        'Sales', 'Order Profit Per Order', 'Benefit per order', 'Sales per customer',
        'Order Item Discount', 'Order Item Product Price', 'Order Item Total', 'Product Price'
    ]
    
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace('$', '').replace(',', '')
        return pd.to_numeric(x, errors='coerce')
        
    for col in financial_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)
            
    # Remove Inconsistent or Zero-Value Records
    critical_id_cols = ['Customer Id', 'Order Id', 'Category Id', 'Product Name']
    df.dropna(subset=[col for col in critical_id_cols if col in df.columns], inplace=True)
    df = df[(df['Sales'] > 0) & (df['Order Item Quantity'] > 0)]
    
    # Derived KPIs
    df['Calculated_Profit_Margin_%'] = (df['Order Profit Per Order'] / df['Sales']) * 100
    
    return df

# Load the data into the app
df = load_and_clean_data()

# --- 2. High-Level KPIs ---
st.header("Key Performance Indicators")

total_revenue = df['Sales'].sum()
total_profit = df['Order Profit Per Order'].sum()
overall_margin = (total_profit / total_revenue) * 100

# Create three columns for top-level metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Overall Profit Margin", f"{overall_margin:.2f}%")

st.divider()

# --- 3. Interactive Charts ---
# Create two side-by-side columns for the charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # --- Category Profitability Bar Chart ---
    category_perf = df.groupby('Category Name').agg({
        'Sales': 'sum',
        'Order Profit Per Order': 'sum'
    }).reset_index()
    
    category_perf['Category Margin (%)'] = (category_perf['Order Profit Per Order'] / category_perf['Sales']) * 100
    category_perf = category_perf.sort_values(by='Order Profit Per Order', ascending=False)
    
    fig_cat = px.bar(
        category_perf,
        x='Category Name',
        y='Order Profit Per Order',
        color='Category Margin (%)',
        title="Profitability by Category (Color-coded by Margin)",
        color_continuous_scale='RdYlGn', 
        height=550
    )
    # Render the plotly chart in Streamlit
    st.plotly_chart(fig_cat, use_container_width=True)

with chart_col2:
    # --- Discount Impact Line Chart ---
    discount_impact = df.groupby('Order Item Discount Rate').agg({
        'Calculated_Profit_Margin_%': 'mean'
    }).reset_index()
    
    fig_disc = px.line(
        discount_impact,
        x='Order Item Discount Rate',
        y='Calculated_Profit_Margin_%',
        title="Discount-Driven Margin Erosion: When do discounts cause losses?",
        markers=True,
        height=550
    )
    # Add Break-Even Line
    fig_disc.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-Even (0% Profit)")
    
    # Render the plotly chart in Streamlit
    st.plotly_chart(fig_disc, use_container_width=True)