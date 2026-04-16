import streamlit as st
from st_supabase_connection import SupabaseConnection

# 1. Page Configuration
st.set_page_config(page_title="Fragrance Discounter", page_icon="🧴", layout="wide")

# 2. Connection Logic
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error: Check your Streamlit Secrets!")
    st.stop()

st.title("✨ Online Fragrance Discounter")

# 3. Sidebar Stats & Brand Filter
with st.sidebar:
    st.header("Project Statistics")
    
    try:
        # Note: Using lowercase table names and columns to match your Supabase image
        brand_res = conn.table("brands").select("*", count="exact").execute()
        frag_res = conn.table("fragrances").select("*", count="exact").execute()
        
        st.metric("Total Brands", len(brand_res.data))
        st.metric("Unique Fragrances", len(frag_res.data))
        
        st.markdown("---")
        st.subheader("Filter by Brand")
        
        # Pulling brandid and brand_name (all lowercase)
        brand_data = conn.table("brands").select("brandid, brand_name").execute()
        brand_list = {item['brand_name']: item['brandid'] for item in brand_data.data}
        selected_brand = st.selectbox("Select a Brand", options=["All"] + list(brand_list.keys()))
        
    except Exception as e:
        st.error(f"Sidebar Error: {e}")
        st.stop()

# 4. Main Search Bar
search_query = st.text_input("Search for a fragrance name...", placeholder="e.g. Aventus")

# 5. Inventory Query (The Relational Join)
try:
    # We use lowercase for EVERYTHING: table names and column names
    builder = conn.table("fragrancevariants").select("""
        price, 
        fragsize, 
        stockamount,
        fragid,
        fragrances (
            frag_name,
            brands (brand_name)
        )
    """)

    # Filter by Brand if selected
    if selected_brand != "All":
        builder = builder.eq("fragid.brandid", brand_list[selected_brand])

    # Filter by Name if searched
    if search_query:
        builder = builder.ilike("fragid.frag_name", f"%{search_query}%")

    results = builder.execute()

    # 6. Display Results
    st.subheader("Current Inventory")
    
    if results.data:
        clean_data = []
        for item in results.data:
            # Safely navigate the nested dictionaries from our join
            frag_info = item.get('fragrances')
            if frag_info:
                brand_info = frag_info.get('brands')
                clean_data.append({
                    "Brand": brand_info['brand_name'] if brand_info else "N/A",
                    "Fragrance": frag_info['frag_name'],
                    "Size": item['fragsize'],
                    "Price": f"${item['price']:,.2f}",
                    "Stock": item['stockamount']
                })
        
        st.dataframe(clean_data, use_container_width=True)
    else:
        st.info("No items found matching your criteria.")

except Exception as e:
    st.error(f"Database Query Error: {e}")
    st.info("Check that RLS (Row Level Security) is disabled or set to Public in Supabase!")
