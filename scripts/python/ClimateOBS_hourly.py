import os
import datetime
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import sys
sys.path.append(f'{os.getcwd()}/scripts/python')
import climate_utils


def format_data(data, source, var):
    match source:
        case 'fwx':
            output = data.pivot(columns='STATION_CODE',index='DATE_TIME',values=var)
            output.index = pd.to_datetime(output.index,format='%Y%m%d%H')
        case 'asp':
            data.columns = data.columns.to_series().apply(lambda x: x.split(" ")[0])
            data.index = pd.to_datetime(data.loc[:,'DATE(UTC)']) - datetime.timedelta(hours=8)
            output = data.drop(columns='DATE(UTC)')
        case 'eccc':
            output = data.loc[:,var].unstack(0)
            output.columns = output.columns.to_series().apply(lambda x: x[1:])
        case 'crd':
            output = data.loc[:,var].unstack(0)
    #Replace any '0' str with 0 (numeric) so not removed by following step:
    output.replace('0',0,inplace = True)
    #Replace any text with NaN:
    output.replace(r'^([A-Za-z]|[0-9]|_)+$', np.NaN, regex=True, inplace=True)
    output = output.astype('float64')
    output.columns = output.columns.astype('str')
    return output

def update_data(data, newdata):
    #Add extra columns for any stations not already in dataframe:
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

def load_data(obj_folder, fname_format, date_list):
    first = True
    for dt_txt in date_list:
        try:
            data_temp = climate_utils.objstore_to_df(os.path.join(obj_folder,fname_format.replace('{dt_txt}',dt_txt)))
        except:
            data_temp = pd.DataFrame()
        if first:
            data = data_temp
            first = False
        else:
            data = pd.concat([data,data_temp])
    return data

def update_climate_obs_raw(dt_list):
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
        ClimateOBS_hrly_raw = climate_utils.objstore_to_df(ClimateOBShourly_raw_path)
        TA_hrly_raw = ClimateOBS_hrly_raw.loc["TA"].copy()
        PC_hrly_raw = ClimateOBS_hrly_raw.loc["PC"].copy()

    crd_objfolder = 'RFC_DATA/CRD/parquet/'
    eccc_objfolder = 'RFC_DATA/ECCC/hourly/parquet/'

    #fwx_objfolder = 'F_WX/extracts/'
    fwx_objfolder = 'F_WX/hourly/'
    asp_objfolder = 'ASP/raw'

    fwx_dt_list = pd.to_datetime(dt_list,format ='%Y%m%d').strftime('%Y-%m-%d')

    eccc_data = load_data(eccc_objfolder,'{dt_txt}.parquet',dt_list)
    crd_data = load_data(crd_objfolder,'{dt_txt}.parquet',dt_list)
    #fwx_data = load_data(fwx_objfolder,'{dt_txt}/{dt_txt}.csv',fwx_dt_list)
    fwx_data = load_data(fwx_objfolder,'{dt_txt}.csv',fwx_dt_list)
    asp_ta = climate_utils.objstore_to_df(os.path.join(asp_objfolder,f'{dt_list[-1]}/TA.csv'))
    asp_pc = climate_utils.objstore_to_df(os.path.join(asp_objfolder,f'{dt_list[-1]}/PC.csv'))

    crd_ta = format_data(crd_data, 'crd', 'air_temp')
    crd_pc = format_data(crd_data, 'crd', 'pcpn_amt_pst1hr')

    eccc_ta = format_data(eccc_data, 'eccc', 'air_temp')
    eccc_pc = format_data(eccc_data, 'eccc', 'pcpn_amt_pst1hr')

    fwx_ta = format_data(fwx_data, 'fwx', 'HOURLY_TEMPERATURE')
    fwx_pc = format_data(fwx_data, 'fwx', 'HOURLY_PRECIPITATION')

    asp_ta = format_data(asp_ta, 'asp','ta')
    asp_pc = format_data(asp_pc, 'asp','pc')
    #ASP data contains data since Oct 1, We only want to import data in import range
    #Find indices of ASP data within import range:
    ind = pd.Series(asp_ta.index.strftime('%Y%m%d').isin(dt_list))
    ind.index = asp_ta.index
    #Subset ASP data to import range:
    asp_ta = asp_ta.loc[ind]
    asp_pc = asp_pc.loc[ind]


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

    climate_utils.df_to_objstore(ClimateOBS_hrly_raw, ClimateOBShourly_raw_path)
    climate_utils.df_to_objstore(TA_hrly_raw, TA_hourly_raw_path)
    climate_utils.df_to_objstore(PC_hrly_raw, PC_hourly_raw_path)

def update_climate_obs_filled(dt_list):
    year = current_date.strftime('%Y')

    objpath = 'ClimateOBS'
    metadata = climate_utils.objstore_to_df(os.path.join(objpath,'metadata','ClimateOBS_metadata.csv'))
    metadata.set_index('ClimateOBS_ID',inplace = True)
    stn_list = metadata.index
    adj_stn_list = climate_utils.objstore_to_df(os.path.join(objpath,'metadata','ClimateOBS_adjacent_stations.csv'))
    adj_stn_list.set_index('STN',inplace = True)

    ClimateOBShourly_filled_path = os.path.join(objpath,f'ClimateOBS_hourly_filled_{year}.parquet')
    TA_hourly_filled_path = os.path.join(objpath,f'TA_hourly_filled_{year}.csv')
    PC_hourly_filled_path = os.path.join(objpath,f'PC_hourly_filled_{year}.csv')

    #Load raw hourly climate obs:
    ClimateOBShourly_raw_path = os.path.join(objpath,f'ClimateOBS_hourly_raw_{year}.parquet')
    ClimateOBS_hrly_raw = climate_utils.objstore_to_df(ClimateOBShourly_raw_path)

    #subset climateobs raw data to import daterange:
    TA_hrly_raw = ClimateOBS_hrly_raw.loc["TA"].copy()
    TA_hrly_raw = TA_hrly_raw[TA_hrly_raw.index.strftime('%Y%m%d').isin(dt_list)]
    PC_hrly_raw = ClimateOBS_hrly_raw.loc["PC"].copy()
    PC_hrly_raw =PC_hrly_raw[PC_hrly_raw.index.strftime('%Y%m%d').isin(dt_list)]

    #Open ClimateOBS filled data. If it does not exist, create a blank dataframe:
    ostore_objs = ostore.list_objects(objpath,return_file_names_only=True)
    if ClimateOBShourly_filled_path not in ostore_objs:
        dt_range = pd.date_range(start = f'{year}/1/1 0:00', end = f'{year}/12/31 23:00', freq = 'H')
        TA_hrly_filled = PC_hrly_filled = pd.DataFrame(data=None,index=dt_range,columns=stn_list,dtype='float64')
    else:
        ClimateOBS_hrly_filled = climate_utils.objstore_to_df(ClimateOBShourly_filled_path)
        TA_hrly_filled = ClimateOBS_hrly_filled.loc["TA"].copy()
        PC_hrly_filled = ClimateOBS_hrly_filled.loc["PC"].copy()
        #Check for differences between metadata station list and ClimateOBS columns?

    TA_hrly_raw[TA_hrly_raw>50] = np.NaN
    TA_hrly_raw[TA_hrly_raw<-50] = np.NaN
    PC_hrly_raw[PC_hrly_raw>50] = np.NaN
    PC_hrly_raw[PC_hrly_raw<0] = np.NaN

    raw_id = metadata.ID.copy()
    ind = metadata.ID.map(lambda calc: len(calc)) == 7
    raw_id[ind] = stn_list[ind]

    TA_na = TA_hrly_raw[:TA_hrly_raw.last_valid_index()].isna()
    NaN_groups = TA_na.ne(TA_na.shift()).cumsum()
    NaN_groups[TA_na==False] = 0
    data_length = len(NaN_groups)
    stn_range = range(len(stn_list))
    #First loop through data gaps; fill any gaps less than 4 hours by interpolating:
    for stn_num in stn_range:
        #Select data for single station:
        if raw_id.iloc[stn_num] in TA_hrly_raw.columns:
            stn_nan_groups = NaN_groups.loc[:,raw_id.iloc[stn_num]]
            nan_groupings = set(stn_nan_groups)
            nan_groupings.discard(0)
            for g in nan_groupings:
                gap_bool = stn_nan_groups==g
                gap_ind = stn_nan_groups.index[gap_bool]
                start_ind = stn_nan_groups.index.get_loc(gap_ind[0])
                stop_ind = stn_nan_groups.index.get_loc(gap_ind[-1])
                gap_length = sum(gap_bool)
                if gap_length <= 3:
                    interp_data = TA_hrly_raw.iloc[max(0,start_ind-1):min(data_length,stop_ind+1)].loc[:,raw_id.iloc[stn_num]].interpolate()
                    TA_hrly_raw.loc[gap_ind,raw_id.iloc[stn_num]] = interp_data.loc[gap_ind]
    #Second loop through data gaps; fill any gaps less than 18 hours with real-time lapse rate:
    #This uses long-term lapse rate, correct to use real-tinme lapse rate!
    #Loop through stations in ClimateOBS:
    for stn_num in stn_range:
        #Check if station has raw data:
        if raw_id.iloc[stn_num] in TA_hrly_raw.columns:
            #Find groups of consecutive NANs in raw data to identify data gaps:
            stn_nan_groups = NaN_groups.loc[:,raw_id.iloc[stn_num]]
            nan_groupings = set(stn_nan_groups)
            nan_groupings.discard(0) #The '0' grouping corresponds to valid numeric data, discard it as we only want data gaps
            #Pull list of adjacent stations to be used for gap filling from metadata:
            adj_stns = adj_stn_list.loc[stn_list[stn_num]][2:8]
            #Loop through the data gaps for each station:
            for g in nan_groupings:
                gap_bool = stn_nan_groups==g
                gap_ind = stn_nan_groups.index[gap_bool]    #indices (datetime) of the missing hourly data in data gap
                gap_length = sum(gap_bool)                  #length of data gap in hours

                fill_stn = ''

                prev_nan_count = float("inf") #Set prev_nan_count to inf so any valid numeric value will replace it in following loop
                #Loop through adjacent stations, checking for valid data over data gap. Station with minimum missing data over the data gap is selected
                for adjstn in adj_stns:
                    if adjstn in TA_hrly_raw.columns:
                        nan_count = sum(TA_hrly_raw.loc[gap_ind,raw_id[adjstn]].isna())
                        if nan_count<prev_nan_count:
                            fill_stn = adjstn
                            prev_nan_count = nan_count
                #Grab any numbers from column name:
                fill_stn_num = ""
                if any(adj_stns==fill_stn):
                    fill_adj_dT = np.nan
                    if gap_length <= 18:
                        gap_start = gap_ind[0]
                        gap_end = gap_ind[-1]
                        training_period = pd.date_range(gap_start- datetime.timedelta(hours=3),gap_start- datetime.timedelta(hours=1),freq='h').union(pd.date_range(gap_end+datetime.timedelta(hours=1),gap_end+datetime.timedelta(hours=3),freq='h'))
                        dT_training_period = TA_hrly_raw.loc[training_period,raw_id[fill_stn]] - TA_hrly_raw.loc[training_period,raw_id.iloc[stn_num]]
                        dT_training_period.dropna(inplace=True)
                        if len(dT_training_period)>0:
                            fill_adj_dT = dT_training_period.mean()
                    if np.isnan( fill_adj_dT):
                        for c in adj_stns.index[adj_stns==fill_stn][0]:
                            if c.isdigit():
                                fill_stn_num = fill_stn_num + c
                        fill_adj_col = 'AVE_dT' + fill_stn_num
                        #Set temperature offset for infill station:
                        fill_adj_dT = adj_stn_list.loc[stn_list[stn_num]][fill_adj_col]
                    #Fill data gap with selected adjacent station after applying temperature offset for that station:
                    TA_hrly_raw.loc[gap_ind,raw_id.iloc[stn_num]] = TA_hrly_raw.loc[gap_ind,raw_id[fill_stn]] + fill_adj_dT
    #Second scan through data gaps:
    #For gaps of 4-18 hours use real-time lapse rate to infill missing data
    #Find adjacent station with minimum number of missing data over missing data period
    #Use 3 hour period on either side of data gap to estimate temperature difference between the two stations











#TO DO:
#Interpolation of missing hourly data
#Calculate daily values
#Shiny app to QC data
if __name__ == '__main__':
    ostore = NRObjStoreUtil.ObjectStoreUtil()

    # default is to use today's date
    #days_back = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))
    days_back = 0
    #Github actions runs in UTC, convert to PST for script to work in github:
    #current_date = datetime.datetime.now() - datetime.timedelta(hours=8) - datetime.timedelta(days=days_back)
    current_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    #If downloading past days, set hour to 23 so entire day is downloaded (scripts only attempts download up to current hour for present day):
    if days_back>0:
        current_date.replace(hour=23)
    #start_date = '2024-05-01'
    start_date = current_date - datetime.timedelta(days=1)
    import_range = pd.date_range(start = start_date, end = current_date, freq = 'D')
    dt_list = import_range.strftime('%Y%m%d')
    update_climate_obs_raw(dt_list)


