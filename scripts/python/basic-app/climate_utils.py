import os
import datetime
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import time

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

def RT_lapse(Station,gap_start_time,gap_end_time):
    gap_start_time = NA_streak_list.iloc[1,1]
    gap_end_time = NA_streak_list.iloc[1,2]
    dt1 = pd.date_range(start = gap_start_time - datetime.timedelta(hours=2), end = gap_start_time, freq = 'H')
    dt2 = pd.date_range(start = gap_end_time, end = gap_end_time + datetime.timedelta(hours=2), freq = 'H')
    RT_training_index = dt1.union(dt2)


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
        TA_hrly_filled = ClimateOBS_hrly_raw.loc["TA"].copy()
        PC_hrly_filled= ClimateOBS_hrly_raw.loc["PC"].copy()

    dt_fillto = current_date.replace(hour=00,minute=00,second=00,microsecond=00)
    TA_hrly_filled = TA_hrly_filled[TA_hrly_filled.index<=dt_fillto]

    start = time.perf_counter()
    test = TA_hrly_filled.copy()
    #Pandas bug mixes column names into
    test.columns = 'C' + test.columns
    test_mask = pd.DataFrame(data=0,index=test.index,columns=test.columns,dtype='int')
    testf = test.copy()
    #Loop though each weather staton (column)
    first = True
    for col in test:
        #Find missing data:
        mask = test.loc[:,col].isna()
        #Cumulative sum goes up by 1 whenver series switches from na to num or vice versa:
        na_df = (mask != mask.shift()).cumsum()
        #Each consecutive streak of NA assigned value equal to length of streak:
        #Mask applied to remove streak values for numeric data
        na_streak = mask.groupby(na_df).transform(lambda x: len(x))* mask
        test_mask.loc[:,col] = na_streak
        #List start and end datestamps of each streak:
        NA_streak_times = (na_df*mask).reset_index().groupby(col).agg(['min','max'])
        NA_streak_times.insert(0,'Station',col)
        if len(NA_streak_times)>0:
            if first:
                NA_streak_list = NA_streak_times
                first = False
            else:
                NA_streak_list = pd.concat([NA_streak_list,NA_streak_times])
    NA_streak_list.reset_index(drop=True,inplace=True)
    NA_streak_list.columns = ['Station','min','max']

    test_interp = test.copy().interpolate()
    testf[test_mask<2] = test_interp[test_mask<=2]
    end = time.perf_counter()
    print(end - start)



