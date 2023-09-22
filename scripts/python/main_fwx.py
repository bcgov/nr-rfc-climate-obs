"""this is the entry point for the retrieval of wildfire data from the federal
governments data mart.
"""

import remote_ostore_sync
import os
import datetime
import logging.config

cur_path = os.path.dirname(__file__)
log_config_path = os.path.join(cur_path, 'logging.config')

logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
LOGGER = logging.getLogger(__name__)
LOGGER.info(f"starting {__name__}")

default_days_from_present = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 1))

current_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present)
yesterday_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present + 1)
current_date_str = current_date.strftime('%Y%m%d')
yesterday_date_str = yesterday_date.strftime('%Y%m%d')

# config local file path
local_file_date_fmt = '%Y%m%d'
date_str = current_date.strftime(local_file_date_fmt)
local_file_path_root = os.getenv('F_WX_DATA_DIR', f'./data/fwx')
local_file_path = os.path.join(local_file_path_root, 'raw')
if not os.path.exists(local_file_path):
    os.makedirs(local_file_path)

cnfig = remote_ostore_sync.SyncRemoteConfig(
    remote_date_fmt='%Y%m%d',
    remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-forestry/{date_str}/',
    ostore_data_dir='F_WX/raw',
    ostore_dir_date_fmt='%Y%m%d',
    local_file_path=local_file_path,
    local_file_date_fmt='%Y%m%d',
    current_date=current_date
)

sync = remote_ostore_sync.SyncRemote(cnfig)
sync.sync()
