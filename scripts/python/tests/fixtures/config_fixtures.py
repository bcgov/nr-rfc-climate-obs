import pytest
import os
import remote_ostore_sync
import logging
import datetime
import shutil

LOGGER = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def remote_ostore_sync_config():
    """sample html representing directory listings"""
    config = remote_ostore_sync.SyncRemoteConfig(
        remote_date_fmt='%Y%m%d',
        remote_location='http://hpfx.collab.science.gc.ca/{date_str}/WXO-DD/observations/swob-ml/partners/bc-forestry/{date_str}/',
        ostore_data_dir='F_WX/raw',
        ostore_dir_date_fmt='%Y%m%d',
        current_date=datetime.datetime.strptime('20230710', '%Y%m%d'),
        local_file_path=os.path.join(os.path.dirname(__file__), 'test_data'),
        local_file_date_fmt='%Y%m%d'
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

@pytest.fixture(scope="function")
def remote_ostore2way_sync():
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data')
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    test_file = os.path.join(test_dir, 'test_file.txt')
    with open(test_file, 'w') as test_file:
        test_file.write('this is a test file')

    another_dir = os.path.join(test_dir, 'another_dir')
    if not os.path.exists(another_dir):
        os.makedirs(another_dir)
    another_file_path = os.path.join(another_dir, 'another_file.txt')
    with open(another_file_path, 'w') as another_file:
        another_file.write('this is another file')

    LOGGER.debug(f"test_dir: {test_dir}")
    ostore_dir = 'TESTS/test_data'
    sync = remote_ostore_sync.SyncProcessed(src_dir=test_dir, ostore_dir=ostore_dir)

    yield sync

    # cleanup
    # if os.path.exists(test_dir):
    #     shutil.rmtree(test_dir)

