"""pulls the vertical elevation profile data (zxs) from the remote location
    and stores it in the ostore.  This is a daily run and is currently being
    run at 8am every day.

- original runs every day at 8am
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

default_days_from_present = int(os.getenv('DEFAULT_DAYS_FROM_PRESENT', 0))

current_date = datetime.datetime.now() - datetime.timedelta(days=default_days_from_present)
current_date_str = current_date.strftime('%Y%m%d')

local_file_path_root = os.getenv('ZXS_DATA_DIR', f'./tmp/zxs')
local_file_path = os.path.join(local_file_path_root, 'raw', "{date_str}")
local_file_date_fmt = '%Y%m%d'

cnfig = remote_ostore_sync.SyncRemoteConfig(
    remote_date_fmt='%Y%m%d',
    remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/vertical_profile/observation/csv/',
    ostore_data_dir='ZXS/',
    ostore_dir_date_fmt='%Y%m%d',
    local_file_path=local_file_path,
    local_file_date_fmt='%Y%m%d',
    current_date=current_date
)

# we only want this file
cnfig.add_file_filter(['ObsTephi_12_CZXS.csv'])

sync = remote_ostore_sync.SyncRemote(cnfig)
sync.sync()

# todo: thinking for other customizations should implement the ability to identify
#       a file filter call back where any custom logic can be applied logic around
#       what should and shouldn't be downloaded. possibly ditto for where they
#       should be stored locally and in ostore.

# when remote_files is provided need to restrict to those files
# https://hpfx.collab.science.gc.ca/20230801/WXO-DD/vertical_profile/observation/csv/
# file to get: ObsTephi_12_CZXS.csv
# rename it: ObsTephi_12_CZXS-%YYYY%-%MT%-%DD%.csv