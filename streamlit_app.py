import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Fragrance Discounter", page_icon="🧴", layout="wide")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error!")
    st.stop()

st.title("✨ Online Fragrance Discounter")

# Sidebar for stats
with st.sidebar:
    st.header("Project Statistics")
    try:
        brand_res = conn.table("brands").select("*", count="exact").execute()
        frag_res = conn.table("fragrances").select("*", count="exact").execute()
        st.metric("Total Brands", len(brand_res.data))
        st.metric("Unique Fragrances", len(frag_res.data))
        
        # BONUS: Low Stock Alert Area
        st.markdown("---")
        st.subheader("⚠️ Low Stock Alerts")
        low_stock = conn.table("fragrancevariants").select("fragsize, stockamount, fragrances(frag_name)").lt("stockamount", 10).execute()
        if low_stock.data:
            for item in low_stock.data:
                st.warning(f"{item['fragrances']['frag_name']} ({item['fragsize']}): Only {item['stockamount']} left!")
        else:
            st.success("All inventory well stocked!")

        st.markdown("---")
        brand_data = conn.table("brands").select("brandid, brand_name").execute()
        brand_list = {item['brand_name']: item['brandid'] for item in brand_data.data}
        selected_brand = st.selectbox("Filter by Brand", options=["All"] + list(brand_list.keys()))
    except:
        st.error("Error loading sidebar.")

# The meaty meat of the website
search_query = st.text_input("Search for a fragrance name...", placeholder="e.g. Sauvage")

try:
    # Query for the frag type
    builder = conn.table("fragrancevariants").select("""
        varianceid, price, fragsize, fragtype, stockamount, fragid,
        fragrances!inner ( frag_name, brandid, brands (brand_name) )
    """)

    if selected_brand != "All":
        builder = builder.eq("fragrances.brandid", brand_list[selected_brand])
    if search_query:
        builder = builder.ilike("fragrances.frag_name", f"%{search_query}%")

    results = builder.execute()

    if results.data:
        for item in results.data:
            frag_info = item['fragrances']
            brand_info = frag_info['brands']
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"### {frag_info['frag_name']}")
                    st.markdown(f"**{brand_info['brand_name']}**")
                    st.caption(f"Size: {item['fragsize']} | Concentration: **{item['fragtype']}**")
                
                with col2:
                    st.write(f"**Price:** ${item['price']:,.2f}")
                    st.write(f"**Stock:** {item['stockamount']} units")
                
                with col3:
                    if st.button("View Scent Notes", key=f"btn_{item['varianceid']}"):
                        note_query = conn.table("fragrancenotes").select("""
                            notes ( notename )
                        """).eq("fragid", item['fragid']).execute()
                        
                        if note_query.data:
                            notes = [n['notes']['notename'] for n in note_query.data]
                            st.info(f"🌿 **Notes:** {', '.join(notes)}")
                        else:
                            st.warning("No notes listed for this scent.")
    else:
        st.info("No fragrances found.")

except Exception as e:
    st.error(f"Logic Error: {e}")

except Exception as e:
    st.error(f"Logic Error: {e}")
