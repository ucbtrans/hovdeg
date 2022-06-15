from utils import *
import streamlit as st
import datetime

# To do
# Display map
# start and end date
# cache plots

init_start_date = datetime.date(2019,3,1)
init_end_date = datetime.date(2019,4,1)

# Initialize .............................
if 'route_name' not in st.session_state:
    st.session_state.route_name = '10Epm46-56'

if 'vds' not in st.session_state:
    st.session_state.vds = 717260

# if 'start_date' not in st.session_state:
#     st.session_state.start_date = init_start_date
#
# if 'end_date' not in st.session_state:
#     st.session_state.end_date = init_end_date


def change_route():
    vdss = load_route_vdss(st.session_state.route_name)
    st.session_state.vds = vdss[0]

# Data loading functions ..........................
@st.cache
def load_route_data(rname,startdate, enddate):
    health = load_health(rname)
    health = health.loc[startdate:enddate]
    vdss = load_route_vdss(rname)
    vds_table = load_route_vds_table(rname)
    return health, vdss, vds_table

@st.cache
def load_vds_data(vdsid,startdate, enddate):
    return load_hourly(vdsid, starttime=startdate, endtime=enddate)

# Plot generating functions ..........................
# @st.cache
def gen_map_route(vdss,vds_table, date):
    return map_route(vdss,vds_table,date)

# @st.cache
def gen_lineplot_route_health(health):
     return lineplot_route_health(health)

# @st.cache
def gen_plot_hourly(hourly):
    return plot_hourly(hourly)

# @st.cache
def gen_lineplot_vds_health(vdsid,health):
    return lineplot_vds_health(vdsid,health, fill=False)

# Load data ..........
route_names = load_route_names()
health, vdss, vds_table = load_route_data(st.session_state.route_name,
                                          st.session_state.start_date,
                                          st.session_state.end_date)

hourly, vds_data = load_vds_data(st.session_state.vds,
                                 st.session_state.start_date,
                                 st.session_state.end_date)

# Render the page ..........

# Route --------------

st.header("Route")

st.selectbox("Route:", route_names, key='route_name', on_change=change_route)

st.date_input(label="Start date:",
              key='start_date',
              value=init_start_date)

st.date_input(label="End date:",
              key='end_date',
              value=init_end_date)

with st.expander("Route map"):
    st.write("UNDER CONSTRUCTION")

with st.expander("Route configuration table"):
    st.write(vds_table)

with st.expander("Route health"):
    st.pyplot(fig=gen_lineplot_route_health(health))

# Stations -------------------
st.header("Stations")
st.selectbox("Select:", vdss, key='vds')

with st.expander("VDS configuration table"):
    st.write(vds_table[vds_table['ID']==st.session_state.vds])

with st.expander("VDS daily health"):
    st.pyplot(fig=gen_lineplot_vds_health(st.session_state.vds, health))

with st.expander("VDS hourly data"):
    st.pyplot(fig=gen_plot_hourly(hourly))
