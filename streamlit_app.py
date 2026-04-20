import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Fragrance Discounter", page_icon="🧴", layout="wide")

# 1. Connection Logic
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error!")
    st.stop()

# 2. Initialize Session State for User Auth
if 'user' not in st.session_state:
    st.session_state.user = None

st.title("✨ Online Fragrance Discounter")

# 3. Sidebar for Auth, Stats, and Filters
with st.sidebar:
    # --- SECTION A: USER AUTHENTICATION ---
    st.header("👤 User Account")
    if st.session_state.user is None:
        auth_tab, sign_up_tab = st.tabs(["Log In", "Sign Up"])
        
        with auth_tab:
            login_first = st.text_input("First Name")
            login_pass = st.text_input("Password", type="password")
            if st.button("Log In"):
                # Querying the users table for matching name and password
                user_query = conn.table("users").select("*").eq("user_first_name", login_first).eq("password", login_pass).execute()
                if user_query.data:
                    st.session_state.user = user_query.data[0]
                    st.success(f"Logged in as {login_first}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try again.")
                    
        with sign_up_tab:
            new_first = st.text_input("New First Name")
            new_last = st.text_input("New Last Name")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                if new_first and new_last and new_pass:
                    conn.table("users").insert({
                        "user_first_name": new_first, 
                        "user_last_name": new_last, 
                        "password": new_pass
                    }).execute()
                    st.success("Account created! Please Log In.")
                else:
                    st.warning("Please fill out all fields.")
    else:
        st.success(f"Logged in: {st.session_state.user['user_first_name']}")
        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    
    # --- SECTION B: PROJECT STATISTICS ---
    st.header("Project Statistics")
    try:
        brand_res = conn.table("brands").select("*", count="exact").execute()
        frag_res = conn.table("fragrances").select("*", count="exact").execute()
        st.metric("Total Brands", len(brand_res.data))
        st.metric("Unique Fragrances", len(frag_res.data))
        
        # Low Stock Alert Area
        st.markdown("---")
        st.subheader("⚠️ Low Stock Alerts")
        low_stock = conn.table("fragrancevariants").select("fragsize, stockamount, fragrances(frag_name)").lt("stockamount", 10).execute()
        if low_stock.data:
            for item in low_stock.data:
                st.warning(f"{item['fragrances']['frag_name']} ({item['fragsize']}): {item['stockamount']} left!")
        else:
            st.success("All inventory well stocked!")

        st.markdown("---")
        
        # --- SECTION C: BRAND FILTER ---
        brand_data = conn.table("brands").select("brandid, brand_name").execute()
        brand_list = {item['brand_name']: item['brandid'] for item in brand_data.data}
        selected_brand = st.selectbox("Filter by Brand", options=["All"] + list(brand_list.keys()))
    except:
        st.error("Error loading sidebar data.")

# 4. Main Tabs (Browsing vs. Wishlist)
main_tab, wishlist_tab = st.tabs(["🛍️ All Fragrances", "❤️ My Wishlist"])

with main_tab:
    search_query = st.text_input("Search for a fragrance name...", placeholder="e.g. Sauvage")

    try:
        # Build query for the inventory
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
                        # BUTTON 1: VIEW NOTES
                        if st.button("Notes", key=f"notes_{item['varianceid']}"):
                            note_q = conn.table("fragrancenotes").select("notes(notename)").eq("fragid", item['fragid']).execute()
                            if note_q.data:
                                notes = [n['notes']['notename'] for n in note_q.data]
                                st.info(f"🌿 **Notes:** {', '.join(notes)}")
                            else:
                                st.warning("No notes found.")
                        
                        # BUTTON 2: WISHLIST (Only visible if logged in)
                        if st.session_state.user:
                            if st.button("❤️ Save", key=f"wish_{item['varianceid']}"):
                                try:
                                    conn.table("wishlist").insert({
                                        "userid": st.session_state.user['userid'],
                                        "varianceid": item['varianceid']
                                    }).execute()
                                    st.toast("Added to Wishlist!")
                                except:
                                    st.toast("Item already in Wishlist!")
                        else:
                            st.caption("Login to save")
        else:
            st.info("No fragrances found.")
    except Exception as e:
        st.error(f"Error: {e}")

with wishlist_tab:
    if st.session_state.user:
        st.subheader(f"Saved for {st.session_state.user['user_first_name']}")
        
        # Advanced Join Query: Wishlist -> Variants -> Fragrances -> Brands
        wish_query = conn.table("wishlist").select("""
            fragrancevariants (
                price, fragsize, fragtype,
                fragrances (frag_name, brands (brand_name))
            )
        """).eq("userid", st.session_state.user['userid']).execute()
        
        if wish_query.data:
            for w in wish_query.data:
                v = w['fragrancevariants']
                st.write(f"💖 **{v['fragrances']['frag_name']}** ({v['fragtype']}) - {v['fragsize']} | ${v['price']}")
        else:
            st.info("Your wishlist is currently empty.")
    else:
        st.info("Please log in via the sidebar to view your wishlist.")
