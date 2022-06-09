import os
import dill
import pandas as pd
import matplotlib.pyplot as plt
import ast
import folium


def get_processed_folder():
    dirname = os.path.dirname(os.path.realpath("__file__"))
    return os.path.join(dirname, '..', 'processed')


def load_routes():

    dirname = os.path.dirname(os.path.realpath("__file__"))
    data_folder = os.path.join(dirname, '..', 'data', 'stationdata')

    with open('routes.txt') as f:
        route_names = ast.literal_eval(f.read())

    routes = {}
    for route_name in route_names:
        try:
            filename = os.path.join(data_folder, f'{route_name}.xlsx')
            df = pd.read_excel(filename)
            routes[route_name] = [int(val) for val in df['ID'].values]
        except:
            print(f"Warning: no station data file for route {route_name}")

    return routes


def load_vds_table(district):

    processed_folder = get_processed_folder()

    with open(os.path.join(processed_folder, f'meta_vds_hist_{district}.pickle'),'rb') as f:
        vds_tables = dill.load(f)

    all_vdss = set(vds_tables.keys())

    cols = ['Fwy', 'Dir', 'District', 'County', 'City', 'State_PM',
            'Abs_PM', 'Latitude', 'Longitude', 'Length', 'Type', 'Lanes', 'Name',
            'User_ID_1', 'User_ID_2', 'User_ID_3', 'User_ID_4']

    vds_table = pd.DataFrame(index=all_vdss, columns=cols)
    for vds, table in vds_tables.items():
        vds_table.loc[vds] = table[cols].iloc[0,:]

    vds_table = vds_table.sort_values('Abs_PM')

    all_vdss = list(vds_table.index)

    return vds_table, all_vdss


def load_vds_tables(districts):
    vds_tables = []
    for district in districts:
        vds_table, _ = load_vds_table(district)
        vds_tables.append(vds_table)
    return pd.concat(vds_tables)


def load_hourly(vds=[], starttime=None, endtime=None):
    # load hourly data for a given vds and time period
    # returns
    # hourly : pandas dataframe with hourly data
    # vdsdata : dictionary with vds static information
    # daily : pandas dataframe with daily health

    if type(vds)==list  and len(vds)==0:
        return None, None, None

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
        return hourly, vdsdata, None

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

    # health information
    daily = hourly['perc_obs'].groupby(hourly.index.to_period('D')).mean() > 80
    daily = daily.to_frame().rename(columns={'perc_obs':'healthy'})

    return hourly, vdsdata, daily


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


def plot_hourly(hourly):
    plt.subplots(figsize=(15, 15), nrows=4, sharex=True)
    plt.subplot(411)
    plt.plot(hourly.index,hourly['perc_obs'])
    plt.ylabel('Perc Obs')
    plt.subplot(412)
    plt.plot(hourly.index,hourly['total_flow'])
    plt.ylabel('Flow [vph]')
    plt.subplot(413)
    plt.plot(hourly.index,hourly['avg_occ'])
    plt.ylabel('Occ [-]')
    plt.subplot(414)
    plt.plot(hourly.index,hourly['avg_speed'])
    plt.ylabel('Speed [XXX]')


def map_route(route_name, dx=0.001, tweakdir='lat'):

    if tweakdir == 'lat':
        latmult = 1.0
        lonmult = 0.0
    else:
        lonmult = 1.0
        latmult = 0.0

    routes = load_routes()
    route = routes[route_name]
    vds_tables = load_vds_tables(get_districts_for_vdss(route))

    small_table = vds_tables.loc[route]
    small_table = small_table.sort_values(by='Abs_PM')

    fig = folium.Figure(width=1000, height=500)
    fmap = folium.Map(location=[small_table['Latitude'].mean(), small_table['Longitude'].mean()],
                      tiles="OpenStreetMap",
                      zoom_start=13).add_to(fig)

    for vds, row in small_table.iterrows():

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

    return fmap
