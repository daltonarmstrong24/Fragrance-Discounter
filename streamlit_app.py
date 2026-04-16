import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Fragrance Discounter", page_icon="🧴", layout="wide")

# 1. Connection
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error. Check your Secrets!")
    st.stop()

st.title("✨ Online Fragrance Discounter")

# 2. Sidebar Stats (REWRITTEN TO FIX YOUR ERROR)
with st.sidebar:
    st.header("Project Statistics")
    
    try:
        # Using .select(count='exact') is more stable than .query("count")
        brand_res = conn.table("brands").select("*", count="exact").execute()
        frag_res = conn.table("fragrances").select("*", count="exact").execute()
        
        st.metric("Total Brands", len(brand_res.data))
        st.metric("Unique Fragrances", len(frag_res.data))
    except Exception as e:
        st.sidebar.warning("Could not load stats. Check table names!")

    st.markdown("---")
    st.subheader("Filter by Brand")
    
    # Get brands for dropdown
    brand_data = conn.table("brands").select("brandID, brand_name").execute()
    brand_list = {item['brand_name']: item['brandID'] for item in brand_data.data}
    selected_brand = st.selectbox("Select a Brand", options=["All"] + list(brand_list.keys()))

# 3. Main Search
search_query = st.text_input("Search for a fragrance name...")

# 4. Main Data Query (REWRITTEN FOR STABILITY)
# Note: Ensure your table names match EXACTLY what is in Supabase (Case Sensitive)
try:
    # Use the table name exactly as it appears in your Supabase dashboard
    # If your table is 'FragranceVariants' with a capital V, change it here:
    builder = conn.table("fragrancevariants").select("""
        price, 
        fragSize, 
        stockAmount,
        Fragrances (
            frag_name,
            Brands (brand_name)
        )
    """)

    if selected_brand != "All":
        builder = builder.eq("fragID.brandID", brand_list[selected_brand])

    if search_query:
        builder = builder.ilike("fragID.frag_name", f"%{search_query}%")

    results = builder.execute()

    # 5. Display
    if results.data:
        clean_data = []
        for item in results.data:
            if item.get('Fragrances'):
                clean_data.append({
                    "brand": item['fragrances']['brands']['brand_name'],
                    "fragrance": item['fragrances']['frag_name'],
                    "size": item['fragSize'],
                    "price": f"${item['price']}",
                    "stock": item['stockAmount']
                })
        st.dataframe(clean_data, use_container_width=True)
    else:
        st.info("No fragrances found.")
        
except Exception as e:
    st.error(f"Data Error: {e}")
    st.info("Tip: Double-check that your table names in the code match Supabase exactly (e.g., 'Brands' vs 'brands').")
