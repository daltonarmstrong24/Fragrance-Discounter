import streamlit as st
from st_supabase_connection import SupabaseConnection

# 1. Page Configuration
st.set_page_config(
    page_title="Fragrance Discounter Project",
    page_icon="🧴",
    layout="wide"
)

# 2. Connection Logic
# This will look for your secrets under [connections.supabase]
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error: Please check your Streamlit Secrets!")
    st.stop()

# 3. App Header
st.title("✨ Online Fragrance Discounter")
st.markdown("---")

# 4. Sidebar Stats & Filters
with st.sidebar:
    st.header("Project Statistics")
    
    # Simple query to show the professor your database is live
    brand_count = conn.query("count", table="brands").execute()
    frag_count = conn.query("count", table="fragrances").execute()
    
    st.metric("Total Brands", brand_count.data[0]['count'])
    st.metric("Unique Fragrances", frag_count.data[0]['count'])
    
    st.markdown("---")
    st.subheader("Filter by Brand")
    # Get brands for a dropdown
    brand_data = conn.query("brandID, brand_name", table="brands").execute()
    brand_list = {item['brand_name']: item['brandID'] for item in brand_data.data}
    selected_brand = st.selectbox("Select a Brand", options=["All"] + list(brand_list.keys()))

# 5. Search Bar Logic
search_query = st.text_input("Search for a fragrance name...", placeholder="Try 'Aventus' or 'Sauvage'")

# 6. Data Retrieval Logic (The Join)
# We select from FragranceVariants because it contains the Price/Stock
# and we join 'upward' to Fragrances and Brands.
query = (
    conn.table("fragrancevariants")
    .select("""
        price, 
        fragsize, 
        stockamount,
        fragrances (
            frag_name,
            brands (brand_name)
        )
    """)
)

# Apply Brand Filter if selected
if selected_brand != "All":
    # We filter using the brandID from our sidebar dict
    query = query.eq("fragrances.brandID", brand_list[selected_brand])

# Apply Search Filter if typed
if search_query:
    query = query.ilike("fragrances.frag_name", f"%{search_query}%")

results = query.execute()

# 7. Displaying the Inventory
st.subheader("Inventory Listing")

if results.data:
    # We clean up the nested JSON so it looks nice in a table
    clean_data = []
    for item in results.data:
        # Check if the nested joins exist to prevent errors
        if item.get('fragrances'):
            clean_data.append({
                "Brand": item['fragrances']['brands']['brand_name'],
                "Fragrance": item['fragrances']['frag_name'],
                "Size": item['fragsize'],
                "Price": f"${item['price']:,.2f}",
                "In Stock": item['stockamount']
            })
    
    # Use Streamlit's native dataframe for a polished look
    st.dataframe(clean_data, use_container_width=True)
else:
    st.info("No items found matching your criteria.")

# 8. Footer (Great for Class Projects)
st.markdown("---")
st.caption("Database Management Class Project - Relational Schema Implementation")
