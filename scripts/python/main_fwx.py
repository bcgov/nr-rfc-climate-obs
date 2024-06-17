"""this is the entry point for the retrieval of wildfire data from the federal
governments data mart.
"""

import datetime
import logging.config
import os

import main_fwx_api
import remote_ostore_sync

# debug params
# if os.path.exists('junk.csv'):
#     os.remove('junk.csv')
# end_date = datetime.datetime(2020, 8, 28, 9, 0, 0)
# fwx_api = main_fwx_api.WildfireAPI(end_date=end_date)
# fwx_api.get_all_stations_hourlies('junk.csv')

# setup the logging
cur_path = os.path.dirname(__file__)
log_config_path = os.path.join(cur_path, 'logging.config')

logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
LOGGER = logging.getLogger(__name__)
LOGGER.info(f"starting {__name__}")

# setting up the time window for pulling data
default_days_from_present = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))
end_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present)
end_date = end_date.replace(
                hour=8,
                minute=0,
                second=0,
                microsecond=0)

# setting up the path to the output data for the local data
local_file_date_fmt = '%Y-%m-%d'
date_str = end_date.strftime(local_file_date_fmt)
local_file_path_root = os.getenv('F_WX_DATA_DIR', './data/fwx')
local_path = os.path.join(local_file_path_root, 'extracts', date_str)
if not os.path.exists(local_path):
    os.makedirs(local_path)
local_file_path = os.path.join(local_path, f'{date_str}.csv')

# ostore paths
ostore_data_dir = 'F_WX/extracts'
ostore_dir_date_fmt = '%Y-%m-%d'
ostore_path = os.path.join(ostore_data_dir, date_str)
ostore_file_path = os.path.join(ostore_path, f'{date_str}.csv')

# sync
ostr_sync = remote_ostore_sync.PushProcessed(src_dir=local_path, ostore_dir=ostore_path)




# don't bother doing anything if the data already exists in object storage
if not ostr_sync.ostore_file_exists(ostore_file_path):

    custom_atribes = [
        ['stationCode', 'station_code'],
        ['', 'STATION_NAME', ''],
        ['weatherTimestamp', 'weather_date'],
        ['precipitation','precipitation'],
        ['temperature', 'temperature'],
        ['relativeHumidity', 'HOURLY_RELATIVE_HUMIDITY'],
        ['windSpeed', 'HOURLY_WIND_SPEED'],
        ['windDirection', 'HOURLY_WIND_DIRECTION'],
        ['windGust', 'HOURLY_WIND_GUST'],
        ['fineFuelMoistureCode', 'HOURLY_FINE_FUEL_MOISTURE_CODE'],
        ['initialSpreadIndex', 'HOURLY_INITIAL_SPREAD_INDEX'],
        ['fireWeatherIndex', 'HOURLY_FIRE_WEATHER_INDEX'],
        ['', 'PRECIPITATION', ''],
        ['', 'FINE_FUEL_MOISTURE_CODE', ''],
        ['', 'INITIAL_SPREAD_INDEX', ''],
        ['', 'FIRE_WEATHER_INDEX', ''],
        ['', 'DUFF_MOISTURE_CODE', ''],
        ['', 'DROUGHT_CODE', ''],
        ['', 'BUILDUP_INDEX', ''],
        ['', 'DANGER_RATING', ''],
        ['', 'RN_1_PLUVIO1', 0],
        ['', 'SNOW_DEPTH', 0],
        ['', 'SNOW_DEPTH_QUALITY', ''],
        ['', 'PRECIP_PLUVIO1_STATUS', 0],
        ['', 'PRECIP_PLUVIO1_TOTAL', 0]
    ]



    # now get the data and store remotely
    fwx_api = main_fwx_api.WildfireAPI(end_date=end_date, download_atribute_config=custom_atribes)
    fwx_api.get_all_stations_hourlies(local_file_path)

    ostr_sync.sync()
