import os
import datetime
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import NRUtil.NRObjStoreUtil as NRObjStoreUtil


def isnumber(x):
    try:
        if str(float(x)) != 'nan':
            return True
        else:
            return False
    except:
        return False

def objstore_to_df(objpath,onprem=False):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    if onprem:
        local_path = objpath
    else:
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
    if not onprem:
        os.remove(local_path)

    return output

def df_to_objstore(df, objpath, onprem=False):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    if onprem:
        local_path = objpath
    else:
        local_folder = 'raw_data/temp_file'
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)
        local_path = os.path.join(local_folder,filename)
    match filetype:
        case 'csv':
            df.to_csv(local_path)
        case 'parquet':
            df.to_parquet(local_path)
    if not onprem:
        ostore.put_object(local_path=local_path, ostore_path=objpath)
        os.remove(local_path)


#Search for desired variables in xml file, grab associated values:
def retrieve_xml_values(xml_file,var_names):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    output = pd.DataFrame(data=None,columns=var_names)
    for child in root.iter():
        if 'name' in child.attrib:
            if child.attrib['name'] in var_names:
                output.loc[0,child.attrib['name']] = child.attrib['value']
    return output

class data_config():
    def __init__(self, objfolder, onprem, stn_list, src_stn_list, url_template, fname_template, var_names):
        self.objfolder = objfolder
        self.onprem = onprem
        self.stn_list = stn_list
        self.src_stn_list = src_stn_list
        self.url_template = url_template
        self.fname_template = fname_template
        self.var_names = var_names

    def update_data(self, date):
        default_date_format = '%Y%m%d'
        dt_txt = date.strftime('%Y%m%d')
        dt_range = pd.date_range(start = date.strftime('%Y/%m/%d 00:00'), end = date.strftime('%Y/%m/%d 23:00'), freq = 'H')
        #Conver dt_range to UTC since data on datamart is in UTC:
        #Limit dt_range_utc to < current time so that it is not trying to grab non-existant data:
        dt_range_utc = dt_range[0:date.hour+1] + datetime.timedelta(hours=8)

        all_data_objpath = os.path.join(self.objfolder,f'{dt_txt}.parquet')
        if self.onprem == False:
            all_data_objs = ostore.list_objects(self.objfolder,return_file_names_only=True)
        else:
            all_data_objs = os.listdir(self.objfolder)
        local_file_path = 'raw_data/temp_data'
        if not os.path.exists(local_file_path):
            os.makedirs(local_file_path)
        if all_data_objpath in all_data_objs:
            #ostore.get_object(local_path=local_data_fpath, file_path=all_data_objpath)
            #output = pd.read_parquet(local_data_fpath)
            output = objstore_to_df(all_data_objpath,self.onprem)
        else:
            output_ind = pd.MultiIndex.from_product([self.src_stn_list,dt_range], names=["Station", "DateTime"])
            output = pd.DataFrame(data=None,index=output_ind,columns=self.var_names+['f_read'])

        #Download ECCC weather observation data from DataMart, store values in dataframe:
        #Loop through each station in station list, each hour in datetime range:
        for stn in self.src_stn_list:
            for dt in dt_range_utc:
                #Format html string for data location:
                dt_str = dt.strftime('%Y-%m-%d-%H00')
                date_str = dt.strftime(default_date_format)

                remote_location = self.url_template.format(date_str=date_str)
                if type(self.fname_template)!=list:
                    self.fname_template=[self.fname_template]
                fname = [str.format(stn=stn,dt_str=dt_str) for str in self.fname_template]
                #file names differs between manual and automated stations, try both:
                full_url = [os.path.join(remote_location,filename) for filename in fname]
                local_filename = os.path.join(local_file_path,f'{stn}-{dt_str}.xml')

                #Download file and write to local file name:
                #Check if file for station/time has already been read in, skip file download if so:
                if output.loc[(stn,dt - datetime.timedelta(hours=8)),'f_read']!=True:
                    #Try filename format for automatic station, else try format for manual station:
                    for url in full_url:
                        with requests.get(url, stream=True) as r:
                            #r.raise_for_status()
                            #If file location exists, proceed with file download:
                            if r.status_code == requests.codes.ok:
                                with open(local_filename, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                break
                    #If file was downloaded succefully, write variables to dataframe:
                    if os.path.exists(local_filename):
                        output.loc[(stn,dt - datetime.timedelta(hours=8)),self.var_names] = retrieve_xml_values(local_filename,self.var_names).values
                        #Set f_read to True so script does not re-download file in subsequent runs:
                        output.loc[stn,dt - datetime.timedelta(hours=8)].iloc[-1] = True
                        os.remove(local_filename)

        #Save dataframe to parquet file and send to object store:
        #output.to_parquet(local_data_fpath)
        #ostore.put_object(local_path=local_data_fpath, ostore_path=all_data_objpath)
        df_to_objstore(output, all_data_objpath, self.onprem)

    def write_data(self,date,objpath,src_varname,out_varname):
        dt_txt = date.strftime('%Y%m%d')
        all_data_objpath = os.path.join(self.objfolder,f'{dt_txt}.parquet')
        #Reformat data for each variable into their own dataframes:
        data = objstore_to_df(all_data_objpath,self.onprem)
        output = data.loc[:,src_varname].unstack(0)[self.src_stn_list]

        #Remove non-numeric (and nan) values:
        output[~output.applymap(isnumber)] = ''

        #Set local and object store filepaths:
        output_obj = os.path.join(objpath,f'{out_varname}_{dt_txt}.csv')

        #Rename station names (for when our desired station names differ from source files):
        output.columns = self.stn_list

        #Save temperature/precip dataframes as csv files and send to object store:
        df_to_objstore(output,output_obj,self.onprem)


if __name__ == '__main__':
    ostore = NRObjStoreUtil.ObjectStoreUtil()

    # default is to use today's date
    days_back = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))
    #days_back = 1
    #Github actions runs in UTC, convert to PST for script to work in github:
    current_date = datetime.datetime.now() - datetime.timedelta(hours=8) - datetime.timedelta(days=days_back)
    #current_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    #If downloading past days, set hour to 23 so entire day is downloaded (scripts only attempts download up to current hour for present day):
    if days_back>0:
        current_date = current_date.replace(hour=23)

    #Grab list of stations to download data for from object store:
    #This is the updated station list for ClimateOBS
    stn_list_local = 'raw_data/ECCC_stationlist.csv'
    #ostore.get_object(local_path=stn_list_local, file_path='RFC_DATA/ECCC/metadata/ECCC_stationlist.csv')
    #stn_metadata = pd.read_csv(stn_list_local)
    stn_metadata = objstore_to_df('RFC_DATA/ECCC/metadata/ECCC_stationlist.csv')
    stn_list = stn_metadata.TC_ID
    src_stn_list = 'C' + stn_list

    #Template for url to download from:
    #url_template = 'https://dd.weather.gc.ca/observations/swob-ml/{date_str}/'
    url_template = 'http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/{date_str}/'

    #Template for file names:
    fname_template = ['{stn}/{dt_str}-{stn}-MAN-swob.xml','{stn}/{dt_str}-{stn}-AUTO-swob.xml']

    #List of variables to grab data for:
    var_names = ['air_temp','avg_air_temp_pst1hr','pcpn_amt_pst1hr']
    objfolder = 'RFC_DATA/ECCC/hourly/parquet/'

    ECCC = data_config(objfolder,False,stn_list,src_stn_list,url_template,fname_template,var_names)
    ECCC.update_data(current_date)

    objpath = 'RFC_DATA/ECCC/hourly/csv/'
    ECCC.write_data(current_date,objpath,'air_temp','TA')
    ECCC.write_data(current_date,objpath,'pcpn_amt_pst1hr','PC')

    crd_objfolder = 'RFC_DATA/CRD/parquet/'
    crd_stn_list = ['fw001','fw003','fw004','fw005','fw006','fw007','fw008','fw009','hy031']
    crd_url_template = 'http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-crd/{date_str}/'
    crd_fname_template = ['{stn}/{dt_str}-bc-crd-{stn}-{stn}-AUTO-swob.xml']
    crd_var_names = ['air_temp','pcpn_amt_pst1hr']
    CRD = data_config(crd_objfolder,False,crd_stn_list,crd_stn_list,crd_url_template,crd_fname_template,crd_var_names)
    CRD.update_data(current_date)

    objpath = 'RFC_DATA/CRD/csv/'
    CRD.write_data(current_date,objpath,'air_temp','TA')
    CRD.write_data(current_date,objpath,'pcpn_amt_pst1hr','PC')
