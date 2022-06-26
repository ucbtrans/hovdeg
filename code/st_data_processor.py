import streamlit as st
from utils_process import *
import logging
import warnings
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

def clear_log():
    with open(LOGFILE, 'w'):
        pass

def run_process_meta():
    logging.warning("Process meta data")
    process_meta(logging,meta_progress_bar,st.session_state)

def run_process_hourly():
    logging.warning("Process hourly_vds data")
    process_hourly(process_routes, logging, hourly_progress_bar,st.session_state)

def run_process_daily():
    logging.warning("Process daily data")
    process_daily(process_routes, logging, daily_progress_bar,st.session_state)

def run_process_all():
    run_process_meta()
    run_process_hourly()
    run_process_daily()

if 'meta_progress' not in st.session_state:
    st.session_state.meta_progress = 0.0

if 'hourly_progress' not in st.session_state:
    st.session_state.hourly_progress = 0.0

if 'daily_progress' not in st.session_state:
    st.session_state.daily_progress = 0.0


# Configuration ..............................................
LOGFILE = 'log_processor.log'
all_route_names = load_route_names()
meta_folder = os.path.join(get_data_folder(), 'meta')
data_folder = get_data_folder()
processed_folder = get_processed_folder()
logging.basicConfig(filename=LOGFILE,
                    encoding='utf-8',
                    level=logging.WARNING,
                    filemode='w')

if ~exists(LOGFILE):
    clear_log()

with st.expander("Configuration"):

    st.subheader("Routes to be processed: ")
    for i, rname in enumerate(all_route_names):
        st.checkbox(rname, value=True, key=f'checkbox{i}')

    st.subheader("Meta data folder: ")
    st.write(meta_folder)

    st.subheader("Traffic data folder: ")
    st.write(data_folder)

    st.subheader("Output folder: ")
    st.write(processed_folder)

# Gather checked route names
process_routes = []
checked=""
for i, rname in enumerate(all_route_names):
    exec(f"checked=st.session_state.checkbox{i}")
    if checked:
        process_routes.append(rname)


# Process all ..............................................
st.button("Process all",on_click=run_process_all)

# Process meta data ..............................................
st.button("Process meta data",on_click=run_process_meta)
meta_progress_bar = st.progress(st.session_state.meta_progress)

# Process hourly_vds data ..............................................
st.button("Process hourly data",on_click=run_process_hourly)
hourly_progress_bar = st.progress(st.session_state.hourly_progress)

# Process daily data ..............................................
st.button("Process health data",on_click=run_process_daily)
daily_progress_bar = st.progress(st.session_state.daily_progress)

# Logging ..............................................
with st.expander("Log"):
    st.button("Clear",on_click=clear_log)
    with open(LOGFILE, "r") as file:
        st.write(file.readlines())