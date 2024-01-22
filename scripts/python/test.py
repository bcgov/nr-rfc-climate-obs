import os
import datetime
import pandas as pd
import NRUtil.NRObjStoreUtil as NRObjStoreUtil

ostore = NRObjStoreUtil.ObjectStoreUtil()

def df_to_objstore(df, objpath):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    local_folder = 'raw_data/temp_file'
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    local_path = os.path.join(local_folder,filename)
    match filetype:
        case 'csv':
            df.to_csv(local_path,index=False)
        case 'parquet':
            df.to_parquet(local_path)

    ostore.put_object(local_path=local_path, ostore_path=objpath)
    os.remove(local_path)


objpath = 'F_WX/extracts'
ostore_objs = ostore.list_objects(objpath,return_file_names_only=True)
for obj in ostore_objs:
    data = objstore_to_df(obj)
    datetxt = data.loc[:,'weather_date'].astype(str)
    hr = datetxt.str[-2:]
    dt = datetxt.str[:-2]
    ind = hr=='99'
    hr[ind]='23'
    datetxt[ind]=dt[ind]+hr[ind]
    data.loc[:,'weather_date']=datetxt
    df_to_objstore(data,obj)
