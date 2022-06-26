from utils_base import *

import warnings
import os
from os.path import exists
import numpy as np
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)


def _check_vds(log, vds_table, vds):

    if len(np.unique(vds_table['Fwy']))>1:
        log.warning(f'VDS {vds} has multiple freeways.')

    if len(np.unique(vds_table['Dir']))>1:
        log.warning(f'VDS {vds} has multiple directions.')

    if len(np.unique(vds_table['District']))>1:
        log.warning(f'VDS {vds} has multiple districts.')

    if len(np.unique(vds_table['County']))>1:
        log.warning(f'VDS {vds} has multiple counties.')

    if len(np.unique(vds_table['State_PM']))>1:
        log.warning(f'VDS {vds} has multiple state PMs.')

    if len(np.unique(vds_table['Abs_PM']))>1:
        log.warning(f'VDS {vds} has multiple absolute PMs.')

    if len(np.unique(vds_table['Latitude']))>1:
        log.warning(f'VDS {vds} has multiple latitude.')

    if len(np.unique(vds_table['Longitude']))>1:
        log.warning(f'VDS {vds} has multiple longitude.')

    if len(np.unique(vds_table['Type']))>1:
        log.warning(f'VDS {vds} has multiple type.')

    if len(np.unique(vds_table['Lanes']))>1:
        log.warning(f'VDS {vds} has multiple lanes.')

def _load_filestable(my_district, hourly_folder):

    rows = list()
    for filename in os.listdir(hourly_folder):

        file_split = os.path.splitext(filename)

        if file_split[1]!='.txt':
            continue

        a = file_split[0].split("_")
        district = int(a[0][1:])
        year = int(a[4])
        month = int(a[5])

        if district!=my_district:
            continue

        rows.append([district,  year, month, filename])

    files_table = pd.DataFrame(rows,columns=['district', 'year', 'month','filename'])
    return files_table

def _compute_hourly_steps(all_districts, route_vdss, hourly_folder):
    steps = 0
    for my_district in all_districts:
        district_table = load_district_config(my_district)
        district_vdss = set(district_table['ID'].values)
        process_vdss = district_vdss.intersection(route_vdss)
        files_table = _load_filestable(my_district, hourly_folder)
        steps += len(process_vdss)*len(files_table)
    return steps

def _compute_daily_steps(routes):
    steps = 0
    for route_name, vdss in routes.items():
        steps += 2*len(vdss)
    return steps

#####################
# PROCESS DATA
#####################

def process_meta(log, meta_progress_bar=None,session_state=None):
    ''' Meta data is always processed for all routes, since it produces files per district'''

    from_streamlit = (meta_progress_bar is not None) and (session_state is not None)

    if from_streamlit:
        session_state.meta_progress = 0.0
        meta_progress_bar.progress(session_state.meta_progress)

    meta_folder = os.path.join(get_data_folder(), 'meta')
    processed_folder = get_processed_folder()
    route_names = load_route_names()
    routes = {rname:load_ordered_route_vdss_from_excel(rname) for rname in route_names}

    # All VDSs to process
    route_vdss = set()
    for route in routes.values():
        if route is not None:
            route_vdss.update( route )

    if from_streamlit:
        session_state.meta_progress = 0.1
        meta_progress_bar.progress(session_state.meta_progress)

    # Gather list of metadata files.
    rows = list()
    for filename in os.listdir(meta_folder):

        file_split = os.path.splitext(filename)

        if file_split[1]!='.txt':
            continue

        a = file_split[0].split("_")
        district = int(a[0][1:])
        year = int(a[3])
        month = int(a[4])
        day = int(a[5])
        rows.append([district,  year, month, day, filename])

    files_table = pd.DataFrame(rows,columns=['district', 'year', 'month', 'day','filename'])

    if from_streamlit:
        session_state.meta_progress = 0.2
        meta_progress_bar.progress(session_state.meta_progress)

    # Create dictionary of district -> VDS ids.
    district2vdss = dict()
    for index, row in files_table.iterrows():

        df = pd.read_csv(os.path.join(meta_folder, row['filename']),sep='\t',dtype={'ID':str})
        district = df.loc[0,'District']

        if district not in district2vdss.keys():
            district2vdss[district] = set()

        dfvds = set(df['ID'].values)
        dfvds = dfvds.intersection(route_vdss)

        district2vdss[district] = district2vdss[district].union(dfvds)

    if from_streamlit:
        session_state.meta_progress = 0.3
        meta_progress_bar.progress(session_state.meta_progress)

    # Gather meta data history for each VDS
    # Save as processed/meta_district_vds_hist_{district}.csv
    for district, vdss in district2vdss.items():

        if len(vdss)==0:
            continue

        vds_tables = dict.fromkeys(vdss)
        district_files = files_table[files_table['district']==district]

        for ind, file_row in district_files.iterrows():

            year = file_row[1]
            month = file_row[2]
            day = file_row[3]
            filename = file_row[4]

            df = pd.read_csv(os.path.join(meta_folder, filename),dtype={'ID':str},sep='\t')

            for vds in district2vdss[district]:
                dfvds = df.loc[df['ID']==vds,:]
                vds_table = vds_tables[vds]

                if vds_table is None:
                    vds_table = dfvds.copy()
                    vds_table.insert(0,'date',pd.Timestamp(year=year,month=month,day=day))
                else:
                    new_row = dfvds.copy()
                    new_row.insert(0,'date',pd.Timestamp(year=year,month=month,day=day))
                    vds_table = pd.concat((vds_table,new_row))

                vds_tables[vds] = vds_table

        # keep differences
        df = pd.DataFrame()
        for vds, vds_table in vds_tables.items():

            # correct State_PM that contain characters
            try:
                state_pm_str = [str(x) for x in vds_table['State_PM']]
                vds_table['State_PM'] = [float(''.join(x for x in str if not x.isalpha())) for str in state_pm_str]
            except:
                log.warning(f"Cannot cast state PM for vds {vds} to float: {vds_table['State_PM']}")

            vds_table.sort_values('date', inplace=True)
            cols = np.setdiff1d(vds_table.columns.values, ('date', 'User_ID_1', 'User_ID_2', 'User_ID_3', 'User_ID_4'))
            np.setdiff1d(vds_table.columns.values, {'date', 'User_ID_1'})
            both_nan = vds_table[cols].shift().isna() & vds_table[cols].isna()
            equal_val = vds_table[cols].shift() == vds_table[cols]

            vds_table = vds_table.loc[~(both_nan | equal_val).all(axis=1)]

            _check_vds(log, vds_table, vds)

            if len(df) == 0:
                df = vds_table
            else:
                df = pd.concat((df, vds_table))

        df.to_csv(filename_vdshist_district(processed_folder, district))

    if from_streamlit:
        session_state.meta_progress = 0.5
        meta_progress_bar.progress(session_state.meta_progress)

    # Tables for routes
    for route_name, vdss in routes.items():

        if vdss==None:
            continue

        districts = get_districts_for_vdss(vdss)
        vds_table = load_districts_config(districts)

        route_table = pd.DataFrame()
        for vds in vdss:
            route_table = pd.concat((route_table, vds_table[vds_table['ID']==vds]))

        route_table.to_csv(filename_vdshist_route(processed_folder, route_name))

    if from_streamlit:
        session_state.meta_progress = 1.0
        meta_progress_bar.progress(session_state.meta_progress)

def process_hourly(route_names, log, hourly_progress_bar=None,session_state=None):

    from_streamlit = (hourly_progress_bar is not None) and (session_state is not None)

    # return if empty route_names
    if len(route_names)==0:
        if from_streamlit:
            session_state.hourly_progress = 1.0
            hourly_progress_bar.progress(session_state.hourly_progress)
        return

    hourly_folder = os.path.join(get_data_folder(), 'hourly')
    processed_folder = get_processed_folder()

    # all vdss to process
    route_vdss = set()
    for rname in route_names:
        route = load_route_config(rname)
        route_vdss.update(route['ID'])

    # get districts covered by these routes
    all_districts = get_districts_for_vdss(route_vdss)

    # initialize progress bar
    if from_streamlit:
        numsteps = _compute_hourly_steps(all_districts, route_vdss, hourly_folder)
        dprog = 1.0/float(numsteps)
        session_state.hourly_progress = 0.0
        hourly_progress_bar.progress(session_state.hourly_progress)

    cols = ['timestamp', 'station', 'district', 'route', 'dir', 'lanetype', 'stn_length', 'samples', 'perc_obs',
            'total_flow', 'avg_occ', 'avg_speed', 'delay_35', 'delay_40', 'delay_45', 'delay_50', 'delay_55', 'delay_60']

    vds2type = {}

    # loop through districts
    for my_district in all_districts:

        print(my_district)

        # vdss to process in this district
        district_table = load_district_config(my_district)
        district_vdss = set(district_table['ID'].values)
        process_vdss = district_vdss.intersection(route_vdss)

        # remove files for these vdss
        for vds in process_vdss:
            filename = filename_hourly_vds(processed_folder, vds)
            if exists(filename):
                os.remove(filename)

        # dictionary of vds to type for this district
        for vds in process_vdss:
            vds_types = district_table.loc[district_table['ID']==vds,'Type'].unique()
            if len(vds_types)>1:
                log.warning(f'VDS{vds} has more than one type: {vds_types}. Choosing {vds_types[0]}')
            vds2type[vds] = vds_types[0]

        # loop through data files for this district
        files_table = _load_filestable(my_district, hourly_folder)
        for index, row in files_table.iterrows():

            # Load the raw data
            pems_data_file = os.path.join(hourly_folder, row['filename'])
            df = pd.read_csv(pems_data_file, header=None, dtype={1:str})
            nrows, ncols = df.shape

            print("\t",pems_data_file)

            # resolve the header for the file
            nlanes = int((ncols-len(cols))/3)
            colnames = cols.copy()
            flw_cols = []
            occ_cols = []
            spd_cols = []
            for lane in range(nlanes):
                colnames.append(f'lane_flw_{lane+1}')
                colnames.append(f'lane_avg_occ_{lane+1}')
                colnames.append(f'lane_avg_spd_{lane+1}')

                flw_cols.append(f'lane_flw_{lane+1}')
                occ_cols.append(f'lane_avg_occ_{lane+1}')
                spd_cols.append(f'lane_avg_spd_{lane+1}')

            df.columns = colnames

            # keep only relevant rows (vdss)
            ind = [vds in process_vdss for vds in df['station']]
            df = df[ind]

            # Drop irrelevant columns
            df = df.drop(columns = flw_cols)
            df = df.drop(columns = occ_cols)
            df = df.drop(columns = spd_cols)
            df = df.drop(columns=['district','delay_35', 'delay_40', 'delay_45', 'delay_50', 'delay_55', 'delay_60'])

            # store in files per vds
            for vds in process_vdss:

                vds_ind = df['station']==vds
                if not vds_ind.any():
                    log.warning(f"{vds} not found in {pems_data_file}")

                df_vds = df[vds_ind].copy()
                df_vds = df_vds.set_index('timestamp')

                # compute VHT, VMT, delay
                if (vds2type[vds]!='OR') and (vds2type[vds]!='FR'):
                    df_vds['VMT'] = df_vds['total_flow'] * df_vds['stn_length']
                    df_vds['VHT'] = df_vds['VMT'] / df_vds['avg_speed']

                # load existing hourly_vds data table and append this one
                hourly_file_name = filename_hourly_vds(processed_folder, vds)
                if exists(hourly_file_name):
                    a = pd.read_csv(hourly_file_name, index_col='timestamp')
                    df_vds = pd.concat((a,df_vds),ignore_index=False, copy=False)  # is it ok to say copy=False?

                # save to file
                df_vds.to_csv(hourly_file_name)

                if from_streamlit:
                    session_state.hourly_progress += dprog
                    session_state.hourly_progress = min(session_state.hourly_progress,1.0)
                    hourly_progress_bar.progress(session_state.hourly_progress)

    # For all vds files, sort the index
    for vds in process_vdss:
        hourly_file_name = filename_hourly_vds(processed_folder, vds)
        if exists(hourly_file_name):
            df_vds = pd.read_csv(hourly_file_name, index_col='timestamp')
            df_vds = df_vds.sort_index()
            df_vds.to_csv(hourly_file_name)

    # Create files per route and per vds type
    for rname in route_names:
        print(rname)
        route = load_route_config(rname)
        route_table = None
        route_type_tables = dict.fromkeys(pems_vds_types)

        for vds in route['ID']:
            hourly_file_name = filename_hourly_vds(processed_folder, vds)
            if not exists(hourly_file_name):
                continue
            df_vds = pd.read_csv(hourly_file_name, index_col='timestamp')

            # append to route_table
            vdstype = vds2type[vds]
            if vdstype in {'ML','HV','FF'}:
                if route_table is None:
                    route_table = pd.DataFrame(index=df_vds.index,columns=['VMT','VHT'])
                route_table = pd.concat((route_table,df_vds[['VMT','VHT']]),axis=1)

                route_type_table = route_type_tables[vdstype]
                if route_type_table is None:
                    route_type_table = pd.DataFrame(index=df_vds.index,columns=['VMT','VHT'])
                route_type_tables[vdstype] = pd.concat((route_type_table,df_vds[['VMT','VHT']]),axis=1)

        # Write route table
        X = pd.DataFrame(index=route_table.index,
                         data={'VMT':route_table['VMT'].sum(axis=1),
                               'VHT':route_table['VHT'].sum(axis=1)})

        X.sort_index(inplace=True)
        X.to_csv(filename_hourly_route(processed_folder, rname))

        # Write route type tables
        for vdstype in {'ML','HV','FF'}:
            route_type_table = route_type_tables[vdstype]
            if route_type_table is None:
                continue
            X = pd.DataFrame(index=route_type_table.index,
                             data={'VMT':route_type_table['VMT'].sum(axis=1),
                                   'VHT':route_type_table['VHT'].sum(axis=1)})
            X.sort_index(inplace=True)
            X.to_csv(filename_hourly_route_vdstype(processed_folder, rname, vdstype))

def process_daily(route_names, log, daily_progress_bar=None,session_state=None):

    from_streamlit = (daily_progress_bar is not None) and (session_state is not None)

    if len(route_names)==0:
        if from_streamlit:
            session_state.daily_progress = 1.0
            daily_progress_bar.progress(session_state.daily_progress)
        return

    processed_folder = get_processed_folder()
    routes = {rname:load_ordered_route_vdss_from_excel(rname) for rname in route_names}

    if from_streamlit:
        dprog = 1.0/float(_compute_daily_steps(routes))
        session_state.daily_progress = 0.0
        daily_progress_bar.progress(session_state.daily_progress)

    # Daily station route_health
    # Save to vds_health_{cfg_name}.csv
    for route_name, vdss in routes.items():

        if vdss is None:
            continue

        # Collect all days from hourly_vds files for these vdss
        days_set = set()
        for vds in vdss:

            filename = filename_hourly_vds(processed_folder, vds)
            if not exists(filename):
                log.warning(f"{filename} not found.")

            try:
                df_vds = pd.read_csv(filename,index_col='timestamp')
                days = set(pd.Timestamp(t).date() for t in df_vds.index)
                days_set.update(days)
            except:
                log.warning(f"Error reading {filename}")

            if from_streamlit:
                session_state.daily_progress += dprog
                session_state.daily_progress = min(session_state.daily_progress,1.0)
                daily_progress_bar.progress(session_state.daily_progress)

        route_days = pd.Series(list(days_set))
        route_days = route_days.sort_values()
        route_config = load_route_config(route_name)

        # dictionary of vds to type for this district
        vds2type = {}
        for vds in vdss:
            print(vds)
            vds_types = route_config.loc[route_config['ID']==vds,'Type'].unique()
            if len(vds_types)>1:
                log.warning(f'VDS{vds} has more than one type: {vds_types}. Choosing {vds_types[0]}')
            if len(vds_types)==0:
                vds2type[vds] = None
            else :
                vds2type[vds] = vds_types[0]

        # vds_health
        route_health = {}
        route_health['route'] = pd.DataFrame(index=route_days, columns=vdss)
        for vdstype in ['OR','FR','ML','HV','FF']:
            route_health[vdstype] = pd.DataFrame(index=route_days,
                                              columns=[k for k,value in vds2type.items() if value==vdstype])

        for vds in vdss:

            vdstype = vds2type[vds]

            try:
                df_vds = pd.read_csv(filename_hourly_vds(processed_folder, vds))
                df_vds['date'] = [pd.Timestamp(t).date() for t in df_vds['timestamp']]

                for day in route_days:
                    ind = df_vds['date']==day
                    X = df_vds.loc[ind,'perc_obs'].mean(skipna=True)
                    route_health['route'].loc[day,vds] = X
                    route_health[vdstype].loc[day,vds] = X

            except Exception as e:
                log.warning(e)

            if from_streamlit:
                session_state.daily_progress += dprog
                session_state.daily_progress = min(session_state.daily_progress,1.0)
                daily_progress_bar.progress(session_state.daily_progress)

        # Save to files
        route_health['route'].to_csv(filename_health_route(processed_folder, route_name))

        for vdstype in ['OR','FR','ML','HV','FF']:
            route_health[vdstype].to_csv(filename_health_routetype(processed_folder, route_name, vdstype))

    if from_streamlit:
        session_state.daily_progress = 1.0
        daily_progress_bar.progress(session_state.daily_progress)
