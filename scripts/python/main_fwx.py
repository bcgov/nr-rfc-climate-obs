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
LOGGER.info("starting main_fwx.py")

default_days_from_present = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 1))

current_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present)
yesterday_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present + 1)
current_date_str = current_date.strftime('%Y%m%d')
yesterday_date_str = yesterday_date.strftime('%Y%m%d')

cnfig = remote_ostore_sync.SyncRemoteConfig(
    remote_date_fmt='%Y%m%d',
    remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-forestry/{date_str}/',
    ostore_dir='F_WX/raw/{date_str}',
    ostore_dir_date_fmt='%Y%m%d',
    current_date=current_date
)

# smaller test config to get the recursive func working
# cnfig = remote_ostore_sync.SyncRemoteConfig(
#     remote_date_fmt='%Y%m%d',
#     remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-RioTinto/{date_str}/',
#     ostore_dir='F_WX/raw/{date_str}',
#     ostore_dir_date_fmt='%Y%m%d',
#     current_date=datetime.datetime.strptime('20230711', '%Y%m%d')
# )

# get the current date string
local_file_path = f'./tmp/raw/{current_date_str}'
if not os.path.exists(local_file_path):
    os.makedirs(local_file_path)

sync = remote_ostore_sync.SyncRemote(cnfig)
root_url = cnfig.calc_root_url()
ostore_path = cnfig.calc_ostore_path()
sync.sync(url=root_url,
          local_file_path=local_file_path,
          ostore_path=ostore_path,
          first_call=True)

# get yesterdays date string
# local_file_path = f'./tmp/raw/{current_date_str}/{yesterday_date_str}'
# if not os.path.exists(local_file_path):
#     os.makedirs(local_file_path)

# cnfig.remote_location = 'http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-forestry/{yesterday_date_str}/'
# cnfig.ostore_dir = 'F_WX/raw/{date_str}/{yesterday_date_str}'
# sync = remote_ostore_sync.SyncRemote(cnfig)
# root_url = cnfig.calc_root_url()
# ostore_path = cnfig.calc_ostore_path()
# sync.sync(url=root_url,
#           local_file_path=local_file_path,
#           ostore_path=ostore_path,
#           first_call=True)
