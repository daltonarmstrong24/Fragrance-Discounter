import streamlit as st
from st_supabase_connection import SupabaseConnection

# 1. Page Configuration
st.set_page_config(page_title="Fragrance Discounter", page_icon="🧴", layout="wide")

# 2. Connection to Supabase
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Connection Error!")
    st.stop()

# 3. Session State for Login Persistence
if 'user' not in st.session_state:
    st.session_state.user = None

st.title("✨ Online Fragrance Discounter")

# 4. Sidebar for Auth, Stats, and Filters
with st.sidebar:
    st.header("👤 User Account")
    if st.session_state.user is None:
        auth_tab, sign_up_tab = st.tabs(["Log In", "Sign Up"])
        with auth_tab:
            l_name = st.text_input("First Name")
            l_pass = st.text_input("Password", type="password")
            if st.button("Log In"):
                u = conn.table("users").select("*").eq("user_first_name", l_name).eq("password", l_pass).execute()
                if u.data:
                    st.session_state.user = u.data[0]
                    st.rerun()
                else: st.error("Invalid Login")
        with sign_up_tab:
            n_first = st.text_input("New First Name")
            n_last = st.text_input("New Last Name")
            n_pass = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                conn.table("users").insert({"user_first_name": n_first, "user_last_name": n_last, "password": n_pass}).execute()
                st.success("Account Created! You can now log in.")

    else:
        st.success(f"Welcome, {st.session_state.user['user_first_name']}!")
        if st.session_state.user.get('is_admin'): 
            st.info("⭐ Admin Mode Active")
        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    
    # Project Statistics
    try:
        brand_res = conn.table("brands").select("*", count="exact").execute()
        frag_res = conn.table("fragrances").select("*", count="exact").execute()
        st.metric("Total Brands", len(brand_res.data))
        st.metric("Unique Fragrances", len(frag_res.data))
        
        st.markdown("---")
        # Brand Filter
        brand_data = conn.table("brands").select("brandid, brand_name").execute()
        brand_dict = {b['brand_name']: b['brandid'] for b in brand_data.data}
        selected_brand = st.selectbox("Filter by Brand", options=["All"] + list(brand_dict.keys()))
    except:
        st.error("Error loading sidebar data.")

# 5. Main Navigation Tabs
tabs_to_show = ["🛍️ Shop", "❤️ Wishlist", "📦 My Orders"]
if st.session_state.user and st.session_state.user.get('is_admin'):
    tabs_to_show.append("🛠️ Admin Panel")

tabs = st.tabs(tabs_to_show)

# --- TAB 1: SHOP ---
with tabs[0]:
    search = st.text_input("Search fragrances...", placeholder="e.g. Aventus")
    
    # Query: Joins Variants -> Fragrances -> Brands
    query = conn.table("fragrancevariants").select("*, fragrances!inner(*, brands(*))")
    
    if selected_brand != "All": 
        query = query.eq("fragrances.brandid", brand_dict[selected_brand])
    if search: 
        query = query.ilike("fragrances.frag_name", f"%{search}%")
    
    try:
        items = query.execute().data
        if items:
            for item in items:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.subheader(item['fragrances']['frag_name'])
                        st.write(f"**{item['fragrances']['brands']['brand_name']}** | {item['fragtype']}")
                        st.caption(f"Size: {item['fragsize']}")
                    with c2:
                        st.write(f"Price: **${item['price']:,.2f}**")
                        st.write(f"Stock: {item['stockamount']} units")
                    with c3:
                        # NOTES BUTTON
                        if st.button("View Notes", key=f"notes_{item['varianceid']}"):
                            note_q = conn.table("fragrancenotes").select("notes(notename)").eq("fragid", item['fragid']).execute()
                            if note_q.data:
                                notes = [n['notes']['notename'] for n in note_q.data]
                                st.info(f"🌿 {', '.join(notes)}")
                        
                        # BUY BUTTON (Decrements stock, creates order & orderdetails)
                        if st.button("🛒 Buy Now", key=f"buy_{item['varianceid']}"):
                            if st.session_state.user:
                                if item['stockamount'] > 0:
                                    # Create Order
                                    new_order = conn.table("orders").insert({"userid": st.session_state.user['userid']}).execute()
                                    oid = new_order.data[0]['orderid']
                                    # Create Order Detail (Matches your schema: orderid, varianceid, quantity, totalcost)
                                    conn.table("orderdetails").insert({
                                        "orderid": oid, "varianceid": item['varianceid'], 
                                        "quantity": 1, "totalcost": item['price']
                                    }).execute()
                                    # Update Stock in Variants table
                                    conn.table("fragrancevariants").update({"stockamount": item['stockamount'] - 1}).eq("varianceid", item['varianceid']).execute()
                                    st.success("Order Placed Successfully!")
                                    st.rerun()
                                else: st.error("Out of stock!")
                            else: st.warning("Please log in to purchase.")
                        
                        # WISHLIST BUTTON
                        if st.session_state.user:
                            if st.button("❤️ Save", key=f"wish_{item['varianceid']}"):
                                try:
                                    conn.table("wishlist").insert({
                                        "userid": st.session_state.user['userid'], 
                                        "varianceid": item['varianceid']
                                    }).execute()
                                    st.toast("Saved to Wishlist!")
                                except:
                                    st.toast("Already in Wishlist!")
        else:
            st.info("No fragrances found.")
    except Exception as e:
        st.error(f"Error fetching inventory: {e}")

# --- TAB 2: WISHLIST ---
with tabs[1]:
    if st.session_state.user:
        st.subheader("Your Saved Items")
        wish = conn.table("wishlist").select("*, fragrancevariants(*, fragrances(*))").eq("userid", st.session_state.user['userid']).execute()
        if wish.data:
            for w in wish.data:
                v = w['fragrancevariants']
                st.write(f"💖 **{v['fragrances']['frag_name']}** - ${v['price']}")
        else: st.write("Wishlist is empty.")
    else: st.info("Log in to view your wishlist.")

# --- TAB 3: ORDER HISTORY ---
with tabs[2]:
    if st.session_state.user:
        st.subheader("Your Order History")
        # Joins Orders -> OrderDetails -> Variants -> Fragrances
        history = conn.table("orders").select("*, orderdetails(*, fragrancevariants(*, fragrances(*)))").eq("userid", st.session_state.user['userid']).execute()
        if history.data:
            for o in history.data:
                with st.expander(f"Order #{o['orderid']} - {o['orderdate'][:10]}"):
                    for d in o['orderdetails']:
                        st.write(f"📦 {d['fragrancevariants']['fragrances']['frag_name']} | ${d['totalcost']}")
        else: st.write("No orders found.")
    else: st.info("Log in to view your orders.")

# --- TAB 4: ADMIN PANEL ---
if "🛠️ Admin Panel" in tabs_to_show:
    with tabs[3]:
        st.header("Inventory Management")
        sub1, sub2 = st.tabs(["Stock Manager", "Add New Item"])
        
        with sub1:
            st.write("Update current inventory levels:")
            all_v = conn.table("fragrancevariants").select("*, fragrances(frag_name)").execute()
            for v in all_v.data:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                col_a.write(f"**{v['fragrances']['frag_name']}** ({v['fragsize']})")
                new_s = col_b.number_input("Stock", value=v['stockamount'], key=f"s_{v['varianceid']}", min_value=0)
                if col_c.button("Update", key=f"save_{v['varianceid']}"):
                    conn.table("fragrancevariants").update({"stockamount": new_s}).eq("varianceid", v['varianceid']).execute()
                    st.toast("Stock Level Updated!")
        
        with sub2:
            st.subheader("Add Fragrance to Database")
            with st.form("add_frag"):
                f_name = st.text_input("Fragrance Name")
                f_brand = st.selectbox("Brand", options=list(brand_dict.values()), format_func=lambda x: [k for k,v in brand_dict.items() if v==x][0])
                if st.form_submit_button("Add Fragrance"):
                    conn.table("fragrances").insert({"frag_name": f_name, "brandid": f_brand}).execute()
                    st.success(f"Added {f_name}! Now use the Table Editor to add its variants/sizes.")
