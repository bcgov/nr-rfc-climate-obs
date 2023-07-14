import pytest
import logging
import os
import dotenv


@pytest.fixture(scope="module")
def nr_ostore(remote_ostore_syncer):
    cur_dir = os.path.dirname(__file__)
    if 'OBJ_STORE_SECRET' not in os.environ:
        # attempt to load secrets from .env file in root directory
        env_file = os.path.join(cur_dir, '..', '..', '..', '.env')
        dotenv.load_dotenv(env_file)
    
