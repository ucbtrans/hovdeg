from utils_load import *
from utils_plot import *
import streamlit as st
from streamlit_folium import st_folium
import datetime
import matplotlib


# Data loading functions ..........................
@st.cache
def load_by_route(rname, starttime, endtime):
    route_vdss = load_ordered_route_vdss_from_excel(rname)
    route_config = load_route_config(rname)
    types_configs = { key:route_config[route_config['Type']==key] for key in ('ML','HV','OR','FR','FF')}
    route_hourly = load_route_hourly(rname, starttime=starttime, endtime=endtime)
    route_vds_health = load_route_vds_health(rname, starttime=starttime, endtime=endtime)
    return route_vdss, route_config, types_configs, route_vds_health, route_hourly

@st.cache
def load_by_type(rname, vds_type, starttime, endtime):
    type_hourly = load_type_hourly(rname, vds_type, starttime=starttime, endtime=endtime)
    type_health = load_type_health(rname, vds_type, starttime=starttime, endtime=endtime)
    return type_hourly, type_health

@st.cache
def load_by_vds(vdsid, starttime, endtime):
    hourly, _ = load_vds_hourly(vdsid, starttime=starttime, endtime=endtime)
    return hourly

# Plot generating functions ..........................

def gen_map_route(vdss,vds_table, date):
    return map_route(vdss,vds_table,date)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_route_health(health):
    return lineplot_route_health(health)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_route_meas(route_meas):
    return lineplot_VMT_VHT(route_meas,figsize=(10, 7))

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_type_health(health):
    return lineplot_type_health(health)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_type_meas(type_meas):
    return lineplot_VMT_VHT(type_meas,figsize=(10, 7))

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_vds_health(vdsid,health):
    return lineplot_vds_health(vdsid,health, fill=False)

@st.cache(hash_funcs={matplotlib.figure.Figure: hash}, suppress_st_warning=True)
def gen_lineplot_vds_meas(hourly_vds):
    return lineplot_vds_meas(hourly_vds)

###### START SCRIPT ######

# Start/End dates -----------

st.date_input(label="Start date:",
              key='start_date',
              value=datetime.date(2019,3,1))

st.date_input(label="End date:",
              key='end_date',
              value=datetime.date(2019,4,1))

# Route --------------

st.header("Route")
st.selectbox("Select:", load_route_names(), key='route_name')

# Load route data
vdss, route_config, types_configs, route_health, route_hourly = load_by_route(st.session_state.route_name,
                                                                              st.session_state.start_date,
                                                                              st.session_state.end_date)

with st.expander("Route map"):
    st_folium(gen_map_route(vdss, route_config, '2019-04-07'), width=1000)  # FIX THIS!

with st.expander("Configuration"):
    st.write(route_config)

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_route_health(route_health))

with st.expander("Measurements"):
    st.pyplot(fig=gen_lineplot_route_meas(route_hourly))

# Stations by type -------------------

st.header("Station by type")
st.selectbox("Select:", ['OR','FR','ML','HV','FF'], key='vds_type')

type_hourly, type_health = load_by_type(st.session_state.route_name,
                                        st.session_state.vds_type,
                                        st.session_state.start_date,
                                        st.session_state.end_date)

with st.expander("Configuration"):
    st.write(types_configs[st.session_state.vds_type])

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_type_health(type_health))

with st.expander("VMT, VHT"):
    if type_hourly is not None:
        st.pyplot(fig=gen_lineplot_type_meas(type_hourly))
    else:
        st.write(f"No VMT, VHT for {st.session_state.vds_type} stations.")

# Individual stations -------------------

st.header("Station by ID")
st.selectbox("Select:", vdss, key='vds')

# Load station data
hourly_vds = load_by_vds(st.session_state.vds,
                         st.session_state.start_date,
                         st.session_state.end_date)

with st.expander("Configuration"):
    st.write(route_config[route_config['ID'] == st.session_state.vds])

with st.expander("Health"):
    st.pyplot(fig=gen_lineplot_vds_health(st.session_state.vds, route_health))

with st.expander("Measurements"):
    st.pyplot(fig=gen_lineplot_vds_meas(hourly_vds))
