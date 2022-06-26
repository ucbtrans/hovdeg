import os
import ast
import pandas as pd
from os.path import exists

pems_vds_types = {'OR','FR','ML','HV','FF'}

def get_data_folder():
    dirname = os.path.dirname(os.path.realpath("__file__"))
    data_folder = os.path.join(dirname, '../data')
    data_folder = os.path.abspath(data_folder)
    return data_folder

def get_processed_folder():
    dirname = os.path.dirname(os.path.realpath("__file__"))
    processed_folder = os.path.join(dirname, '../processed')
    processed_folder = os.path.abspath(processed_folder)
    return processed_folder

def load_route_names():
    try:
        with open('routes.txt') as f:
            route_names = ast.literal_eval(f.read())
    except:
        print("Error loading routes.txt")
    return route_names

def filename_vdshist_district(processed_folder, district):
    return os.path.join(processed_folder, f'vdshist_district_{district}.csv')

def filename_vdshist_route(processed_folder, route_name):
    return os.path.join(processed_folder, f'vdshist_route_{route_name}.csv')

def filename_hourly_vds(processed_folder, vds):
    return os.path.join(processed_folder,f'hourly_{vds}.csv')

def filename_hourly_route(processed_folder, rname):
    return os.path.join(processed_folder,f'hourly_{rname}.csv')

def filename_hourly_route_vdstype(processed_folder, rname, vdstype):
    return os.path.join(processed_folder,f'hourly_{rname}_{vdstype}.csv')

def filename_health_route(processed_folder, route_name):
    return os.path.join(processed_folder,f'health_{route_name}.csv')

def filename_health_routetype(processed_folder, route_name, vdstype):
    return os.path.join(processed_folder,f'health_{route_name}_{vdstype}.csv')


###################
# LOAD ROUTE CONFIG
###################

def load_route_config(route_name):
    X = pd.read_csv(filename_vdshist_route(get_processed_folder(), route_name),
                    index_col=0,
                    parse_dates=[1],
                    dtype={'ID':str})
    return X

def load_ordered_route_vdss_from_excel(route_name):
    dirname = os.path.dirname(os.path.realpath("__file__"))
    data_folder = os.path.join(dirname, '..', 'data', 'stationdata')
    filename = os.path.join(data_folder, f'{route_name}.xlsx')

    if not exists(filename):
        print(f"Error: {filename} does not exist.")
        return None

    try:
        df = pd.read_excel(filename)
        route_data = [str(val) for val in df['ID'].values]
    except Exception as e:
        print(e)
    return route_data


###################
# LOAD DISTRICT CONFIG
###################

def load_district_config(district):
    return pd.read_csv(filename_vdshist_district(get_processed_folder(), district),
                       index_col=0,
                       parse_dates=[1],
                       dtype={'ID':str})

def load_districts_config(districts):
    vds_tables = []
    for district in districts:
        vds_table = load_district_config(district)
        vds_tables.append(vds_table)
    return pd.concat(vds_tables)


###################
# DISTRICT FOR VDS
###################

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

def get_vds2distict_map(vdss):
    return { str(vds):get_district_for_vds(vds) for vds in vdss }
