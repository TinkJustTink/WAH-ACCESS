import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="WAH Line Access Guide",
    page_icon="🛤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def parse_mileage_to_decimal(m_str):
    if pd.isna(m_str):
        return None
    m_str = str(m_str).replace('½', '.5').replace('¼', '.25').replace('¾', '.75')
    match = re.search(r'M\s*(\d+)\s*C\s*([\d\.]+)', m_str)
    if match:
        miles = float(match.group(1))
        chains = float(match.group(2))
        return miles + (chains / 80.0)
    return None

st.title("🛤️ WAH Access & GPS Guide")
st.markdown("Interactive site layout and navigation tool.")

# --- CONNECTING TO YOUR GOOGLE DRIVE ---
@st.cache_data
def load_data():
    # 📑 REPLACE THE URL BELOW WITH YOUR GOOGLE DRIVE DIRECT DOWNLOAD URL
    google_drive_url = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID_HERE"
    
    df = pd.read_excel(google_drive_url)
    df['DECIMAL_MILES'] = df['MILLAGE'].apply(parse_mileage_to_decimal)
    return df

try:
    df = load_data()
    
    st.sidebar.header("🔍 Search & Filter")
    st.sidebar.subheader("🎯 Find Nearest Access")
    calc_mode = st.sidebar.checkbox("Activate Mileage Calculator")
    
    nearest_site_idx = None
    if calc_mode:
        target_m = st.sidebar.number_input("Target Mile", min_value=0, max_value=300, value=145)
        target_c = st.sidebar.number_input("Target Chain", min_value=0.0, max_value=79.9, value=0.0, step=1.0)
        target_decimal = target_m + (target_c / 80.0)
        
        valid_miles = df.dropna(subset=['DECIMAL_MILES'])
        if not valid_miles.empty:
            idx_closest = (valid_miles['DECIMAL_MILES'] - target_decimal).abs().idxmin()
            closest_row = df.loc[idx_closest]
            st.sidebar.success(f"Closest point: {closest_row['PLACE NAME']} ({closest_row['MILLAGE']})")
            
            if st.sidebar.button("Show Nearest Access Info"):
                nearest_site_idx = idx_closest

    st.sidebar.markdown("---")
    
    access_types = ["All"] + sorted(df["ACCESS ON TO LINE"].dropna().unique().tolist())
    selected_access = st.sidebar.selectbox("Access on to Line", access_types)
    search_query = st.sidebar.text_input("Search Site / Place / Road", "").strip().lower()
    
    if nearest_site_idx is not None:
        filtered_df = df.loc[[nearest_site_idx]]
        st.info(f"Showing the closest access point to your mileage query.")
    else:
        filtered_df = df.copy()
        if selected_access != "All":
            filtered_df = filtered_df[filtered_df["ACCESS ON TO LINE"] == selected_access]
            
        if search_query:
            filtered_df = filtered_df[
                filtered_df["PLACE NAME"].str.lower().fillna("").str.contains(search_query) |
                filtered_df["ROAD / STREET"].str.lower().fillna("").str.contains(search_query) |
                filtered_df["SITE DETAILS / ACCESS INSTRUCTIONS"].str.lower().fillna("").str.contains(search_query) |
                filtered_df["MILLAGE"].str.lower().fillna("").str.contains(search_query)
            ]

    if nearest_site_idx is None:
        st.metric(label="Total Matching Sites", value=len(filtered_df))
    
    if filtered_df.empty:
        st.warning("No sites found matching your current criteria.")
    else:
        for idx, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 4, 2])
                with col1:
                    st.markdown(f"**📍 {row['MILLAGE']}**")
                with col2:
                    st.markdown(f"### {row['PLACE NAME']}")
                with col3:
                    coords = str(row['GPS COORDINATES']).replace(" ", "")
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={coords}"
                    st.link_button("🌐 Open Google Maps", maps_url, type="primary")
                
                meta1, meta2, meta3 = st.columns(3)
                meta1.write(f"**Line Side:** {row['ACCESS ON TO LINE']}")
                meta2.write(f"**Road/Street:** {row['ROAD / STREET']}")
                meta3.write(f"**Coordinates:** `{row['GPS COORDINATES']}`")
                
                st.markdown(f"> **Access Instructions:** {row['SITE DETAILS / ACCESS INSTRUCTIONS']}")
                st.markdown("---")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")

