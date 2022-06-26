from utils import *
import streamlit as st
import datetime
import matplotlib

# To do
# Display map
# start and end date
# cache plots

init_start_date = datetime.date(2019,3,1)
init_end_date = datetime.date(2019,4,1)

# Initialize .............................
if 'route_name' not in st.session_state:
    st.session_state.route_name = '99Npm287-301'

if 'vds' not in st.session_state:
    st.session_state.vds = 319482

if 'start_date' not in st.session_state:
    st.session_state.start_date = init_start_date

if 'end_date' not in st.session_state:
    st.session_state.end_date = init_end_date

if 'vds_type' not in st.session_state:
    st.session_state.station_type = 'ML'


def change_route():
    vdss = load_route_vdss_from_excel(st.session_state.route_name)
    st.session_state.vds = vdss[0]

# Data loading functions ..........................
@st.cache
def load_route_data(rname,startdate, enddate):
    health = load_route_health(rname)
    health = health.loc[startdate:enddate]
    vdss = load_route_vdss_from_excel(rname)
    vds_table = load_route_config(rname)
    vds_types = { key:vds_table[vds_table['Type']==key] for key in ('ML','HV','OR','FR')}
    return health, vdss, vds_table, vds_types

@st.cache
def load_vds_data(vdsid,startdate, enddate):
    return load_vds_meas(vdsid, starttime=startdate, endtime=enddate)

# Plot generating functions ..........................

def gen_map_route(vdss,vds_table, date):
    return map_route(vdss,vds_table,date)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_route_health(health):
     return lineplot_route_health(health)


@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_type_health(vds_table_type, health):
    return lineplot_type_health(vds_table_type, health)


@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_type_meas(hourly):
    return lineplot_type_meas(hourly)


@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_vds_health(vdsid,health):
    return lineplot_vds_health(vdsid,health, fill=False)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_vds_meas(hourly):
    return lineplot_vds_meas(hourly)


# Load data ..........
route_names = load_route_names()
health, vdss, vds_table, vds_types = load_route_data(st.session_state.route_name,
                                          st.session_state.start_date,
                                          st.session_state.end_date)

hourly, vds_data = load_vds_data(st.session_state.vds,
                                 st.session_state.start_date,
                                 st.session_state.end_date)

# Render the page ..........

# Route --------------

st.date_input(label="Start date:",
              key='start_date',
              value=init_start_date)

st.date_input(label="End date:",
              key='end_date',
              value=init_end_date)

st.header("Route")

st.selectbox("Select:", route_names, key='route_name', on_change=change_route)


# with st.expander("Route map"):
#     st_folium(gen_map_route(vdss, route_config, '2019-07-07'), width=1000)


with st.expander("Configuration"):
    st.write(vds_table)

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_route_health(health))

with st.expander("Measurements"):
    st.write("UNDER CONSTRUCTION")

# Groups of stations -------------------

st.header("Station by type")
st.selectbox("Select:", ['OR','FR','ML','HV'], key='vds_type')

vds_table_type = vds_types[st.session_state.station_type]

with st.expander("Configuration"):
    st.write(vds_table_type)

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_type_health(vds_table_type, health))


with st.expander("Measurements"):
    st.write("UNDER CONSTRUCTION")

# Individual stations -------------------
st.header("Station by ID")
st.selectbox("Select:", vdss, key='vds')

with st.expander("Configuration"):
    st.write(vds_table[vds_table['ID']==st.session_state.vds])

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_vds_health(st.session_state.vds, health))

with st.expander("Measurements"):
    st.pyplot(fig=gen_lineplot_vds_meas(hourly))
