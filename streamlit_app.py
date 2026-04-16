import streamlit as st
from st_supabase_connection import SupabaseConnection

# 1. Page Config
st.set_page_config(page_title="Fragrance Discounter", page_icon="✨")
st.title("✨ Online Fragrance Discounter")

# 2. Initialize Connection
conn = st.connection("supabase", type=SupabaseConnection)

# 3. Sidebar - Admin/Status
with st.sidebar:
    st.header("Shop Stats")
    # Quick count of fragrances
    count_res = conn.query("*", table="fragrances", count="exact").execute()
    st.metric("Total Fragrances", len(count_res.data))

# 4. Main UI - Search Section
search_query = st.text_input("Search for a fragrance or brand...", placeholder="e.g. Dior")

# 5. Data Display Logic
if search_query:
    # This searches the 'frag_name' column for your query
    res = conn.table("fragrances").select("*, brands(brand_name)").ilike("frag_name", f"%{search_query}%").execute()
else:
    # Default view: Show everything joined with brands
    res = conn.table("fragrances").select("frag_name, brands(brand_name)").execute()

# 6. Render as a clean table
if res.data:
    # Flatten the brand name out of the nested dictionary for a better look
    formatted_data = [
        {"Fragrance": row['frag_name'], "Brand": row['brands']['brand_name']} 
        for row in res.data
    ]
    st.dataframe(formatted_data, use_container_width=True)
else:
    st.warning("No fragrances found matching that search.")
