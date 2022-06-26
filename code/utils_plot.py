import pandas as pd
import matplotlib.pyplot as plt
import folium
import numpy as np

########################
# PLOTS
########################

# BY ROUTE

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

    map_table_nonans = map_table.dropna()

    if len(map_table_nonans)!=len(map_table):
        dropped = map_table.index.difference(map_table_nonans.index)
        print(f'WARNING: These stations lack location data and are not included in the map: {dropped.values}')

    fig = folium.Figure(width=1000, height=500)
    fmap = folium.Map(location=[map_table_nonans['lat'].mean(), map_table_nonans['lng'].mean()],
                      tiles="OpenStreetMap",
                      zoom_start=13).add_to(fig)

    for vds, row in map_table_nonans.iterrows():

        if row['type'] == 'HV':
            icon = folium.Icon(color="green")
            tweak = dx
        elif row['type'] == 'ML':
            icon = folium.Icon(color="red")
            tweak = 0
        elif row['type'] == 'OR':
            icon = folium.Icon(color="blue")
            tweak = -dx
        elif row['type'] == 'FR':
            icon = folium.Icon(color="purple")
            tweak = -2*dx
        else:
            icon = folium.Icon(color="black")
            tweak = 0

        folium.Marker(
            location=(row['lat'] + latmult*tweak, row['lng'] + lonmult*tweak),
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
    plt.ylabel('% route health', fontsize=16)
    plt.grid()
    return fig

def lineplot_VMT_VHT(meas, figsize=(15, 5)):
    fig, ax = plt.subplots(figsize=figsize, nrows=2, sharex=True)
    plt.subplot(211)
    plt.plot(meas.index,meas['VMT'])
    plt.grid()
    plt.ylabel('VMT')
    plt.subplot(212)
    plt.plot(meas.index,meas['VHT'])
    plt.grid()
    plt.ylabel('VHT')
    return fig

# BY TYPE

def lineplot_type_health(health_table, fill=False, figsize=(15, 5)):

    fig = plt.figure(figsize=figsize)

    if fill:
        plt.fill_between(health_table.index,health_table.mean(axis=1))
    else:
        health_table.mean(axis=1).plot(linewidth=2)

    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    plt.ylabel('% route health', fontsize=16)
    plt.grid()
    return fig

# BY VDS

def lineplot_vds_health(vds,health_table, fill=False, figsize=(15,5)):
    fig = plt.figure(figsize=figsize)

    if fill:
        plt.fill_between(health_table.index,health_table[str(vds)])
    else:
        health_table[str(vds)].plot(linewidth=2)

    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    plt.ylabel('% VDS health', fontsize=16)
    plt.grid()
    return fig

def lineplot_vds_meas(hourly,figsize=(10, 15)):
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


