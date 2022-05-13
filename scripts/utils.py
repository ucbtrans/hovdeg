import os
import dill
import pandas as pd

def load_vds_table(processed_folder,district):

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

