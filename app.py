import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(page_title="Avian Biodiversity Analysis Dashboard", layout="wide")
st.title("🦅 Bird Species Observation & Conservation Dashboard")
st.markdown("Comparative analysis platform across Forest and Grassland habitats.")

# Connect to SQL Database
@st.cache_data
def load_sql_data():
    engine = create_engine('sqlite:///bird_observations.db')
    return pd.read_sql("SELECT * FROM bird_observations", engine)

df = load_sql_data()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("Filter Options")

# Administrative Unit Filter
admin_list = ['All'] + sorted(list(df['Admin_Unit_Code'].dropna().unique()))
selected_admin = st.sidebar.selectbox("Administrative Unit Code", admin_list)

# Habitat Type Filter (Forest vs Grassland)
habitat_list = ['All'] + sorted(list(df['Location_Type'].dropna().unique()))
selected_habitat = st.sidebar.selectbox("Habitat Type", habitat_list)

# SAFE YEAR FILTER (Prevents slider crash when min_yr == max_yr)
min_yr = int(df['Year'].min()) if not df['Year'].dropna().empty else 2018
max_yr = int(df['Year'].max()) if not df['Year'].dropna().empty else 2018

if min_yr < max_yr:
    selected_years = st.sidebar.slider("Observation Year Range", min_yr, max_yr, (min_yr, max_yr))
else:
    st.sidebar.info(f"Observation Year: **{min_yr}**")
    selected_years = (min_yr, max_yr)

# Watchlist Filter Toggle
watchlist_only = st.sidebar.checkbox("Show At-Risk Species Only (PIF Watchlist)")

# Apply Filtering Logic
filtered_df = df.copy()
if selected_admin != 'All':
    filtered_df = filtered_df[filtered_df['Admin_Unit_Code'] == selected_admin]
if selected_habitat != 'All':
    filtered_df = filtered_df[filtered_df['Location_Type'] == selected_habitat]

filtered_df = filtered_df[(filtered_df['Year'] >= selected_years[0]) & (filtered_df['Year'] <= selected_years[1])]

if watchlist_only:
    filtered_df = filtered_df[filtered_df['PIF_Watchlist_Status'] == True]

# ---------------- METRIC DASHBOARD CARDS ----------------
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Sightings", f"{len(filtered_df):,}")
m2.metric("Unique Species", filtered_df['Scientific_Name'].nunique())
m3.metric("Plots Monitored", filtered_df['Plot_Name'].nunique())
m4.metric("At-Risk Species", filtered_df[filtered_df['PIF_Watchlist_Status'] == True]['Scientific_Name'].nunique())
m5.metric("Avg Temp (°F)", f"{filtered_df['Temperature'].mean():.1f}")

st.markdown("---")

# ---------------- INTERACTIVE ANALYSIS TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 Spatial & Species Diversity", 
    "⏰ Temporal Patterns & Observers", 
    "🌤️ Weather & Environmental Impact", 
    "🛡️ Conservation Insights",
    "📄 Cleaned Data Explorer"
])

# TAB 1: SPATIAL & SPECIES
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 Most Common Bird Species")
        top_spp = filtered_df['Common_Name'].value_counts().head(10).reset_index()
        top_spp.columns = ['Species', 'Sightings']
        fig_spp = px.bar(top_spp, x='Sightings', y='Species', orientation='h', 
                         color='Sightings', color_continuous_scale='Viridis')
        fig_spp.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_spp, use_container_width=True)
        
    with c2:
        st.subheader("Observations by Habitat Type")
        fig_hab = px.pie(filtered_df, names='Location_Type', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_hab, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Detection Identification Methods")
        fig_id = px.histogram(filtered_df, x='ID_Method', color='Location_Type', barmode='group')
        st.plotly_chart(fig_id, use_container_width=True)
    with c4:
        st.subheader("Distance Class vs Flyover Activity")
        fig_fly = px.histogram(filtered_df, x='Distance', color='Flyover_Observed')
        st.plotly_chart(fig_fly, use_container_width=True)

# TAB 2: TEMPORAL & OBSERVER
with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Annual Sighting Trends")
        yr_trend = filtered_df.groupby('Year').size().reset_index(name='Count')
        fig_yr = px.bar(yr_trend, x='Year', y='Count')
        st.plotly_chart(fig_yr, use_container_width=True)
        
    with col_b:
        st.subheader("Monthly Seasonality Breakdown")
        mth_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        mth_trend = filtered_df.groupby('Month_Name').size().reindex(mth_order).dropna().reset_index(name='Count')
        fig_mth = px.bar(mth_trend, x='Month_Name', y='Count', color='Count', color_continuous_scale='Blues')
        st.plotly_chart(fig_mth, use_container_width=True)

    st.subheader("Top Observer Sighting Counts")
    obs_df = filtered_df['Observer'].value_counts().head(10).reset_index()
    obs_df.columns = ['Observer', 'Reports']
    fig_obs = px.bar(obs_df, x='Observer', y='Reports', color='Reports')
    st.plotly_chart(fig_obs, use_container_width=True)

# TAB 3: ENVIRONMENTAL IMPACT
with tab3:
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.subheader("Temperature (°F) vs. Sighting Density")
        fig_temp = px.histogram(filtered_df, x="Temperature", color="Location_Type", nbins=20, marginal="rug")
        st.plotly_chart(fig_temp, use_container_width=True)
    with col_e2:
        st.subheader("Impact of Disturbance Levels on Counts")
        fig_dist = px.histogram(filtered_df, x="Disturbance", color="Location_Type", barmode="group")
        st.plotly_chart(fig_dist, use_container_width=True)

# TAB 4: CONSERVATION INSIGHTS
with tab4:
    st.subheader("Partners in Flight (PIF) Watchlist At-Risk Species")
    watchlist_df = filtered_df[filtered_df['PIF_Watchlist_Status'] == True]
    
    if not watchlist_df.empty:
        wl_summary = watchlist_df.groupby(['Common_Name', 'Scientific_Name', 'AOU_Code']).size().reset_index(name='Sightings').sort_values(by='Sightings', ascending=False)
        
        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            st.dataframe(wl_summary, use_container_width=True)
        with col_w2:
            fig_wl = px.pie(wl_summary.head(10), names='Common_Name', values='Sightings', title="Top At-Risk Species Share")
            st.plotly_chart(fig_wl, use_container_width=True)
    else:
        st.info("No at-risk watchlist species match the active filters.")

# TAB 5: RAW DATA EXPLORER
with tab5:
    st.subheader("SQL Master Dataset View")
    st.dataframe(filtered_df)
