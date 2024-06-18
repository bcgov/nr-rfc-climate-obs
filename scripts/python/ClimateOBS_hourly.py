import os
import datetime
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil

def df_to_objstore(df, objpath):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    local_folder = 'raw_data/temp_file'
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    local_path = os.path.join(local_folder,filename)
    match filetype:
        case 'csv':
            df.to_csv(local_path)
        case 'parquet':
            df.to_parquet(local_path)

    ostore.put_object(local_path=local_path, ostore_path=objpath)
    os.remove(local_path)

def objstore_to_df(objpath):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    local_folder = 'raw_data/temp_file'
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    local_path = os.path.join(local_folder,filename)
    ostore.get_object(local_path=local_path, file_path=objpath)
    match filetype:
        case 'csv':
            output = pd.read_csv(local_path)
        case 'parquet':
            output = pd.read_parquet(local_path)
    os.remove(local_path)

    return output

def format_data(data, source, var):
    match source:
        case 'fwx':
            output = data.pivot(columns='station_code',index='weather_date',values=var)
            output.index = pd.to_datetime(output.index,format='%Y%m%d%H') - datetime.timedelta(hours=8)
        case 'asp':
            data.columns = data.columns.to_series().apply(lambda x: x.split(" ")[0])
            data.index = pd.to_datetime(data.loc[:,'DATE(UTC)']) - datetime.timedelta(hours=8)
            output = data.drop(columns='DATE(UTC)')
        case 'eccc':
            output = data.loc[:,var].unstack(0)
            output.columns = output.columns.to_series().apply(lambda x: x[1:])
        case 'crd':
            output = data.loc[:,var].unstack(0)
    output.replace(r'^([A-Za-z]|[0-9]|_)+$', np.NaN, regex=True, inplace=True)
    output = output.astype('float64')
    output.columns = output.columns.astype('str')
    return output

def update_data(data, newdata):
    if len(data.columns)>0:
        old_col = set(data.columns)
        new_col = [x for x in newdata.columns if x not in old_col]
    else:
        new_col = newdata.columns
    if len(new_col)>0:
        new_col_df = pd.DataFrame(data=None,index=data.index,columns=new_col)
        data = pd.concat([data,new_col_df],axis=1)
    index_intersect = data.index.intersection(newdata.index)
    #newdata = newdata.loc[index_intersect]
    #data.loc[newdata.index,newdata.columns]=newdata
    data.loc[index_intersect,newdata.columns]=newdata.loc[index_intersect]

    return data


#TO DO:
#Interpolation of missing hourly data
#Calculate daily values
#Shiny app to QC data
if __name__ == '__main__':
    ostore = NRObjStoreUtil.ObjectStoreUtil()

    # default is to use today's date
    #days_back = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))
    days_back = 1
    #Github actions runs in UTC, convert to PST for script to work in github:
    #current_date = datetime.datetime.now() - datetime.timedelta(hours=8) - datetime.timedelta(days=days_back)
    current_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    #If downloading past days, set hour to 23 so entire day is downloaded (scripts only attempts download up to current hour for present day):
    if days_back>0:
        current_date.replace(hour=23)
    dt_txt = current_date.strftime('%Y%m%d')

    year = current_date.strftime('%Y')

    objpath = 'ClimateOBS'
    ClimateOBShourly_raw_path = os.path.join(objpath,f'ClimateOBS_hourly_raw_{year}.parquet')
    TA_hourly_raw_path = os.path.join(objpath,f'TA_hourly_raw_{year}.csv')
    PC_hourly_raw_path = os.path.join(objpath,f'PC_hourly_raw_{year}.csv')
    ostore_objs = ostore.list_objects(objpath,return_file_names_only=True)
    #Create raw temperature and precipitation dataframes for current year if they do not currently exist:
    if ClimateOBShourly_raw_path not in ostore_objs:
        dt_range = pd.date_range(start = f'{year}/1/1 0:00', end = f'{year}/12/31 23:00', freq = 'H')
        TA_hrly_raw = PC_hrly_raw = pd.DataFrame(data=None,index=dt_range,columns=None,dtype='float64')
    else:
        ClimateOBS_hrly_raw = objstore_to_df(ClimateOBShourly_raw_path)
        TA_hrly_raw = ClimateOBS_hrly_raw.loc["TA"].copy()
        PC_hrly_raw = ClimateOBS_hrly_raw.loc["PC"].copy()

    crd_objfolder = 'RFC_DATA/CRD/parquet/'
    eccc_objfolder = 'RFC_DATA/ECCC/hourly/parquet/'
    fwx_objfolder = 'F_WX/extracts/'
    asp_objfolder = 'ASP/raw'

    objfolder_list = [crd_objfolder, eccc_objfolder]

    crd_data = objstore_to_df(os.path.join(crd_objfolder,f'{dt_txt}.parquet'))
    crd_ta = format_data(crd_data, 'crd', 'air_temp')
    crd_pc = format_data(crd_data, 'crd', 'pcpn_amt_pst1hr')

    eccc_data = objstore_to_df(os.path.join(eccc_objfolder,f'{dt_txt}.parquet'))
    eccc_ta = format_data(eccc_data, 'eccc', 'air_temp')
    eccc_pc = format_data(eccc_data, 'eccc', 'pcpn_amt_pst1hr')

    fwx_dt_txt = (current_date+datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    fwx_data = objstore_to_df(os.path.join(fwx_objfolder,f'{fwx_dt_txt}/{fwx_dt_txt}.csv'))
    fwx_ta = format_data(fwx_data, 'fwx', 'temperature')
    fwx_pc = format_data(fwx_data, 'fwx', 'precipitation')

    asp_ta = objstore_to_df(os.path.join(asp_objfolder,f'{dt_txt}/TA.csv'))
    asp_ta = format_data(asp_ta, 'asp','ta')
    asp_pc = objstore_to_df(os.path.join(asp_objfolder,f'{dt_txt}/PC.csv'))
    asp_pc = format_data(asp_pc, 'asp','pc')

    #Check that all data is in correct time zone!
    TA_hrly_raw =update_data(TA_hrly_raw,fwx_ta)
    TA_hrly_raw =update_data(TA_hrly_raw,asp_ta)
    TA_hrly_raw =update_data(TA_hrly_raw,eccc_ta)
    TA_hrly_raw =update_data(TA_hrly_raw,crd_ta)

    PC_hrly_raw =update_data(PC_hrly_raw,fwx_pc)
    PC_hrly_raw =update_data(PC_hrly_raw,asp_pc)
    PC_hrly_raw =update_data(PC_hrly_raw,eccc_pc)
    PC_hrly_raw =update_data(PC_hrly_raw,crd_pc)

    TA_hrly_raw = TA_hrly_raw.astype('float64')
    PC_hrly_raw = PC_hrly_raw.astype('float64')
    ClimateOBS_hrly_raw = pd.concat([TA_hrly_raw,PC_hrly_raw],keys=["TA","PC"])
    df_to_objstore(ClimateOBS_hrly_raw, ClimateOBShourly_raw_path)
    df_to_objstore(TA_hrly_raw, TA_hourly_raw_path)
    df_to_objstore(PC_hrly_raw, PC_hourly_raw_path)
