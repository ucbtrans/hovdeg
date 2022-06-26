from utils_base import *

def _select_time_rows(table, starttime=None, endtime=None):
    if starttime==None and endtime==None:
        return table
    elif starttime==None:
        return table[:endtime]
    elif endtime==None:
        return table[starttime:]
    else:
        return table[starttime:endtime]

###################
# DATA BY ROUTE
###################

def load_route_hourly(route_name, starttime=None, endtime=None):
    filename = filename_hourly_route(get_processed_folder(),route_name)
    table = pd.read_csv(filename,dtype={'route':str, 'perc_obs':float},index_col='timestamp')
    table.index = pd.to_datetime(table.index)
    table = _select_time_rows(table, starttime, endtime)
    return table

def load_route_vds_health(route_name, starttime=None, endtime=None):
    filename = filename_health_route(get_processed_folder(), route_name)
    table = pd.read_csv(filename, parse_dates=True, index_col=0).fillna(0)
    table = _select_time_rows(table, starttime, endtime)
    return table

#####################
# DATA BY TYPE
#####################

def load_type_hourly(route_name, vds_type, starttime=None, endtime=None):

    if vds_type=='OR' or vds_type=='FR':
        return None

    filename = filename_hourly_route_vdstype(get_processed_folder(),route_name,vds_type)
    hourly = pd.read_csv(filename,dtype={'route':str, 'perc_obs':float},index_col='timestamp')
    hourly.index = pd.to_datetime(hourly.index)
    hourly = _select_time_rows(hourly, starttime, endtime)
    return hourly

def load_type_health(route_name, vds_type, starttime=None, endtime=None):
    filename = filename_health_routetype(get_processed_folder(), route_name, vds_type)
    table = pd.read_csv(filename, parse_dates=True, index_col=0).fillna(0)
    return _select_time_rows(table, starttime, endtime)

#####################
# DATA BY VDS
#####################

def load_vds_hourly(vds, starttime=None, endtime=None):

    filename = filename_hourly_vds(get_processed_folder(),vds)
    hourly = pd.read_csv(filename,dtype={'route':str, 'perc_obs':float},index_col='timestamp')
    hourly.index = pd.to_datetime(hourly.index)
    hourly = hourly.drop(labels=['samples','station'],axis=1)
    hourly = _select_time_rows(hourly, starttime, endtime)

    vdsdata = {'vds': str(vds)}
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



