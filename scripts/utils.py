import os
import pandas as pd
import matplotlib.pyplot as plt
import ast
import folium
from os.path import exists
import numpy as np


def get_processed_folder():
    dirname = os.path.dirname(os.path.realpath("__file__"))
    return os.path.join(dirname, '..', 'processed')


def load_route_names():
    try:
        with open('routes.txt') as f:
            route_names = ast.literal_eval(f.read())
    except:
        print("Error loading routes.txt")
    return route_names

###################
# ROUTE VDS
###################

def load_route_vds_table(route_name):
    return pd.read_csv(os.path.join(get_processed_folder(), f'meta_route_vds_hist_{route_name}.csv'),
                       index_col=0,
                       parse_dates=[1])


def load_route_vdss(route_name):
    dirname = os.path.dirname(os.path.realpath("__file__"))
    data_folder = os.path.join(dirname, '..', 'data', 'stationdata')
    filename = os.path.join(data_folder, f'{route_name}.xlsx')

    if not exists(filename):
        print(f"Error: {filename} does not exist.")
        return None

    try:
        df = pd.read_excel(filename)
        route_data = [int(val) for val in df['ID'].values]
    except Exception as e:
        print(e)
    return route_data


def load_routes_vdss(route_names):
    routes = {}
    for route_name in route_names:
        routes[route_name] = load_route_vdss(route_name)

    return routes

###################
# DISTRICT VDS
###################

def load_district_vds_table(district):
    return pd.read_csv(os.path.join(get_processed_folder(), f'meta_district_vds_hist_{district}.csv'),
                         index_col=0,
                         parse_dates=[1])


def load_districts_vds_tables(districts):
    vds_tables = []
    for district in districts:
        vds_table = load_district_vds_table(district)
        vds_tables.append(vds_table)
    return pd.concat(vds_tables)


def get_district_for_vds(vds):
    possible_answers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    strvds = str(vds)
    guess = int(strvds[:-5])
    if guess in possible_answers:
        return guess
    else:
        guess = int(strvds[:-6])
        if guess in possible_answers:
            return guess
        else:
            return 0


def get_districts_for_vdss(vdss):
    return {get_district_for_vds(vds) for vds in vdss}


def get_vds2district_map(vdss):
    return { vds:get_district_for_vds(vds) for vds in vdss }

########################
# TRAFFIC DATA
########################

def load_hourly(vds, starttime=None, endtime=None):
    # load hourly data for a given vds and time period
    # returns
    # hourly : pandas dataframe with hourly data
    # vdsdata : dictionary with vds static information
    # daily : pandas dataframe with daily health

    processed_folder = get_processed_folder()

    # Load data
    filename = os.path.join(processed_folder,f'{vds}_hourly.csv')
    hourly = pd.read_csv(filename)
    hourly = hourly.astype({'route':str, 'perc_obs':float})
    hourly['timestamp'] = pd.to_datetime(hourly['timestamp'])
    hourly = hourly.set_index('timestamp')
    hourly = hourly.drop(labels=['samples','station'],axis=1)

    # select time rows
    if starttime!=None and endtime!=None:
        hourly = hourly.loc[starttime:endtime]
    elif starttime!=None:
        hourly = hourly.loc[starttime:]
    elif endtime!=None:
        hourly = hourly.loc[:endtime]

    vdsdata = {'vds': vds}
    if len(hourly)==0:
        return hourly, vdsdata

    # keep vds metadata
    if len(hourly['route'].unique())>1:
        vdsdata['route'] = hourly['route']
        print("WARNING: route changed in the given period")
    else:
        vdsdata['route'] = hourly['route'][0]
        hourly = hourly.drop(labels='route',axis=1)

    if len(hourly['dir'].unique())>1:
        vdsdata['dir'] = hourly['dir']
        print("WARNING: direction changed in the given period")
    else:
        vdsdata['dir'] = hourly['dir'][0]
        hourly = hourly.drop(labels='dir',axis=1)

    if len(hourly['lanetype'].unique())>1:
        vdsdata['lanetype'] = hourly['lanetype']
        print("WARNING: lane type changed in the given period")
    else:
        vdsdata['lanetype'] = hourly['lanetype'][0]
        hourly = hourly.drop(labels='lanetype',axis=1)

    if len(hourly['stn_length'].unique())>1:
        vdsdata['stn_length'] = hourly['stn_length']
        print("WARNING: station length changed in the given period")
    else:
        vdsdata['stn_length'] = hourly['stn_length'][0]
        hourly = hourly.drop(labels='stn_length',axis=1)

    return hourly, vdsdata


def load_health(route_name, startday=None, endday=None):
    processed_folder = get_processed_folder()
    filename = os.path.join(processed_folder, f'route_health_{route_name}.csv')
    table = pd.read_csv(filename, index_col=0, parse_dates=True)
    if startday==None and endday==None:
        return table
    elif startday==None:
        return table[:endday]
    elif endday==None:
        return table[startday:]
    else:
        return table[startday:endday]

########################
# PLOTS
########################

def plot_hourly(hourly,figsize=(10, 15)):
    fig, ax = plt.subplots(figsize=figsize, nrows=4, sharex=True)
    plt.subplot(411)
    plt.plot(hourly.index,hourly['perc_obs'])
    plt.grid()
    plt.ylabel('Perc Obs')
    plt.subplot(412)
    plt.plot(hourly.index,hourly['total_flow'])
    plt.grid()
    plt.ylabel('Flow [vph]')
    plt.subplot(413)
    plt.plot(hourly.index,hourly['avg_occ'])
    plt.grid()
    plt.ylabel('Occ [-]')
    plt.subplot(414)
    plt.plot(hourly.index,hourly['avg_speed'])
    plt.grid()
    plt.ylabel('Speed [mph]')
    return fig


def map_route(vdss, vds_table, date, dx=0.001, tweakdir='lat'):

    if tweakdir == 'lat':
        latmult = 1.0
        lonmult = 0.0
    else:
        lonmult = 1.0
        latmult = 0.0

    map_table = pd.DataFrame(index=vdss,columns=['lat','lng','type'])
    for vds in vdss:

        ind = vds_table['ID']==vds
        if ~np.any(ind):
            continue

        if sum(ind)==1:
            map_table.loc[vds, ['lat','lng','type']] = vds_table.loc[ind,['Latitude','Longitude','Type']].values
        else:
            tiny_table = vds_table.loc[ind,['date','Latitude','Longitude','Type']]
            first_post = np.where(tiny_table['date']>date)
            if len(first_post[0])==0:
                last_pre = 0
            else:
                last_pre = np.max(first_post[0][0]-1,0)

            map_table.loc[vds, ['lat','lng','type']] = tiny_table.iloc[last_pre,[1,2,3]].values

    fig = folium.Figure(width=1000, height=500)
    fmap = folium.Map(location=[vds_table['Latitude'].mean(), vds_table['Longitude'].mean()],
                      tiles="OpenStreetMap",
                      zoom_start=13).add_to(fig)

    for vds, row in vds_table.iterrows():

        if row['Type'] == 'HV':
            icon = folium.Icon(color="green")
            tweak = dx
        elif row['Type'] == 'ML':
            icon = folium.Icon(color="red")
            tweak = 0
        elif row['Type'] == 'OR':
            icon = folium.Icon(color="blue")
            tweak = -dx
        elif row['Type'] == 'FR':
            icon = folium.Icon(color="purple")
            tweak = -2*dx
        else:
            icon = folium.Icon(color="black")
            tweak = 0

        folium.Marker(
            location=(row['Latitude'] + latmult*tweak, row['Longitude'] + lonmult*tweak),
            popup=vds,
            icon=icon
        ).add_to(fmap)

    return fig


def pcolor_route_health(health_table, figsize=(15,8)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.pcolor(health_table.index,health_table.columns,health_table.T,cmap='gray')
    ax.invert_yaxis()
    return fig


def lineplot_route_health(health_table, fill=False, figsize=(15, 5)):
    fig = plt.figure(figsize=figsize)

    if fill:
        plt.fill_between(health_table.index,health_table.mean(axis=1))
    else:
        health_table.mean(axis=1).plot(linewidth=2)

    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    plt.ylabel('% health', fontsize=16)
    plt.grid()
    return fig


def lineplot_vds_health(vds,health_table, fill=False, figsize=(15,5)):
    fig = plt.figure(figsize=figsize)

    if fill:
        plt.fill_between(health_table.index,health_table[str(vds)])
    else:
        health_table[str(vds)].plot(linewidth=2)

    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    plt.ylabel('% health', fontsize=16)
    plt.grid()
    return fig

