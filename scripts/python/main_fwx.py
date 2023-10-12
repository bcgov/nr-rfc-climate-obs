"""this is the entry point for the retrieval of wildfire data from the federal
governments data mart.
"""

import datetime
import logging.config
import os

import main_fwx_api
import remote_ostore_sync

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
local_file_path_root = os.getenv('F_WX_DATA_DIR', f'./data/fwx/extracts')
local_path = os.path.join(local_file_path_root, date_str)
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

    # now get the data and store remotely
    fwx_api = main_fwx_api.WildfireAPI(end_date=end_date)
    fwx_api.get_all_stations_hourlies(local_file_path)

    ostr_sync.sync()
