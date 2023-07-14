import pytest
import os
import remote_ostore_sync
import logging
import datetime

LOGGER = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def remote_ostore_sync_config():
    """sample html representing directory listings"""
    config = remote_ostore_sync.SyncRemoteConfig(
        remote_date_fmt='%Y%m%d',
        remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-forestry/{date_str}/',
        ostore_dir='F_WX/raw',
        ostore_dir_date_fmt='%Y%m%d',
        current_date=datetime.datetime.strptime('20230710', '%Y%m%d')
    )
    yield config

@pytest.fixture(scope="function")
def remote_ostore_syncer(remote_ostore_sync_config):
    LOGGER.debug("got here")
    cur_dir = os.path.dirname(__file__)
    if 'OBJ_STORE_SECRET' not in os.environ:
        # attempt to load secrets from .env file in root directory
        env_file = os.path.join(cur_dir, '..', '..', '..', '.env')
        dotenv.load_dotenv(env_file)

    rs = remote_ostore_sync.SyncRemote(remote_ostore_sync_config)
    yield rs
