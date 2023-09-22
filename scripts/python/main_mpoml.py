import remote_ostore_sync
import os
import datetime
import logging.config

# logging setup
cur_path = os.path.dirname(__file__)
log_config_path = os.path.join(cur_path, 'logging.config')
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
LOGGER = logging.getLogger(__name__)
LOGGER.info(f"starting {__name__}")

default_date_format = '%Y%m%d'

# default is to use today's date
default_days_from_present = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))
current_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present)

# config local file path
date_str = current_date.strftime(default_date_format)
local_file_path_root = os.getenv('MPOML_DATA_DIR', f'./data')
# the sync function will automatically prepend the date onto the local path
local_file_path = os.path.join(local_file_path_root, 'raw')
local_file_date_fmt = '%Y%m%d'
if not os.path.exists(local_file_path):
    os.makedirs(local_file_path)

# https://hpfx.collab.science.gc.ca/20230921/observations/xml/BC/today/today_bc_20230921_e.xml
cnfig_today = remote_ostore_sync.SyncRemoteConfig(
    remote_date_fmt='%Y%m%d',
    remote_location='http://hpfx.collab.science.gc.ca/{date_str}/observations/xml/BC/today',
    # sync function will prepend the date onto the function
    ostore_data_dir='MPOML/raw',
    ostore_dir_date_fmt='%Y%m%d',
    local_file_path=local_file_path,
    local_file_date_fmt='%Y%m%d',
    current_date=current_date
)
cnfig_today.add_file_filter([f'today_bc_{date_str}_e.xml'])

sync = remote_ostore_sync.SyncRemote(cnfig_today)
sync.sync()

cnfig_yesterday = cnfig_today
cnfig_yesterday.remote_location = 'http://hpfx.collab.science.gc.ca/{date_str}/observations/xml/BC/yesterday'
cnfig_yesterday.file_filter = [f'yesterday_bc_{date_str}_e.xml']
sync = remote_ostore_sync.SyncRemote(cnfig_yesterday)
sync.sync()
