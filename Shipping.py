import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Shipping Intelligence Dashboard", layout="wide")

st.title("📦 Shipping Intelligence Dashboard")
st.markdown("Advanced Analytics for Factory-to-Customer Efficiency")

# LOAD DATA
df = pd.read_csv("Nassau Candy Distributor.csv")

df.columns = df.columns.str.strip()

df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
df['Ship Date'] = pd.to_datetime(df['Ship Date'], dayfirst=True)

df['lead_time'] = (df['Ship Date'] - df['Order Date']).dt.days
df = df[df['lead_time'] >= 0]

df['route'] = df['Division'] + " → " + df['State/Province']

# STATE CODE FIX (IMPORTANT)
state_code_map = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT',
    'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL',
    'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
    'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND',
    'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
    'Pennsylvania': 'PA', 'Rhode Island': 'RI',
    'South Carolina': 'SC', 'South Dakota': 'SD',
    'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

df['state_code'] = df['State/Province'].map(state_code_map)

# SIDEBAR FILTERS
st.sidebar.header("Smart Filters")

start_date = st.sidebar.date_input("Start Date", df['Order Date'].min())
end_date = st.sidebar.date_input("End Date", df['Order Date'].max())

region = st.sidebar.multiselect("Region", df['Region'].unique(), default=df['Region'].unique())
state = st.sidebar.multiselect("State", df['State/Province'].unique())
ship_mode = st.sidebar.multiselect("Ship Mode", df['Ship Mode'].unique(), default=df['Ship Mode'].unique())

lead_range = st.sidebar.slider(
    "Lead Time Range",
    0,
    int(df['lead_time'].max()),
    (0, int(df['lead_time'].max()))
)
# APPLY FILTERS
filtered_df = df[
    (df['Order Date'] >= pd.to_datetime(start_date)) &
    (df['Order Date'] <= pd.to_datetime(end_date)) &
    (df['Region'].isin(region)) &
    (df['Ship Mode'].isin(ship_mode)) &
    (df['lead_time'] >= lead_range[0]) &
    (df['lead_time'] <= lead_range[1])
]

if state:
    filtered_df = filtered_df[filtered_df['State/Province'].isin(state)]

# KPIs
st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Shipments", len(filtered_df))
col2.metric("Avg Lead Time", round(filtered_df['lead_time'].mean(), 2))
col3.metric("Max Lead Time", filtered_df['lead_time'].max())

# HEATMAP
st.subheader("US Geographic Shipping Efficiency")

state_analysis = filtered_df.groupby('state_code')['lead_time'].mean().reset_index()

fig_map = px.choropleth(
    state_analysis,
    locations='state_code',
    locationmode="USA-states",
    color='lead_time',
    scope="usa",
    color_continuous_scale="Reds"
)

st.plotly_chart(fig_map, use_container_width=True)

# ROUTE PERFORMANCE
st.subheader("Route Performance Leaderboard")

route_perf = filtered_df.groupby('route')['lead_time'].agg(['mean', 'count']).reset_index()
route_perf.columns = ['route', 'avg_lead_time', 'total_shipments']

top_routes = route_perf.sort_values(by='avg_lead_time').head(10)
worst_routes = route_perf.sort_values(by='avg_lead_time', ascending=False).head(10)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Top Efficient Routes")
    st.dataframe(top_routes)

with col2:
    st.markdown("### 🔴 Bottleneck Routes")
    st.dataframe(worst_routes)

st.subheader("💰 Cost vs Lead Time Analysis")

cost_analysis = filtered_df.groupby('Ship Mode').agg({
    'lead_time': 'mean',
    'Cost': 'mean'
}).reset_index()

fig_cost = px.scatter(
    cost_analysis,
    x='Cost',
    y='lead_time',
    color='Ship Mode',
    size='lead_time',
    title="Cost vs Delivery Time Tradeoff"
)

st.plotly_chart(fig_cost, use_container_width=True)

# SHIP MODE ANALYSIS
st.subheader("Shipping Mode Efficiency")

ship_mode_analysis = filtered_df.groupby('Ship Mode')['lead_time'].mean().reset_index()

fig_ship = px.bar(
    ship_mode_analysis,
    x='Ship Mode',
    y='lead_time',
    color='Ship Mode',
    title="Lead Time by Shipping Mode"
)

st.plotly_chart(fig_ship, use_container_width=True)

# ORDER TIMELINE
st.subheader("Order Timeline Analysis")

timeline = filtered_df.groupby('Order Date')['lead_time'].mean().reset_index()

fig_time = px.line(
    timeline,
    x='Order Date',
    y='lead_time',
    title="Lead Time Trend Over Time"
)

st.plotly_chart(fig_time, use_container_width=True)

# DRILL DOWN
st.subheader("State-Level Drill Down")

selected_state = st.selectbox("Select State", filtered_df['State/Province'].unique())

state_df = filtered_df[filtered_df['State/Province'] == selected_state]

st.dataframe(state_df[['Order Date', 'Ship Date', 'lead_time', 'Ship Mode', 'route']])

# BOTTLENECK ALERTS
st.subheader("Bottleneck Alerts")

high_delay = route_perf[route_perf['avg_lead_time'] > route_perf['avg_lead_time'].mean()]

st.warning(f"{len(high_delay)} routes are performing worse than average!")

# INSIGHTS
st.subheader("Key Insights")

st.markdown("""
- 🚚 Standard shipping shows slightly better efficiency than expedited methods  
- 🌍 Southern regions exhibit higher delivery delays  
- 🔴 Certain routes act as bottlenecks and need optimization  
- 📈 Lead time variability suggests inconsistent logistics performance  
""")