import pytest
import remote_ostore_sync
import logging
import os

LOGGER = logging.getLogger(__name__)

def test_dir_parser(dirs_html, remote_ostore_syncer):
    rs = remote_ostore_syncer
    dirList = rs._parse_html(dirs_html)
    LOGGER.debug(f"dirList: {dirList}")

def test_file_parser(files_html, remote_ostore_syncer):
    rs = remote_ostore_syncer
    dirList = rs._parse_html(files_html)
    LOGGER.debug(f"dirList: {dirList}")

@pytest.mark.parametrize("file_url", [
    
        'https://hpfx.collab.science.gc.ca/20230707/WXO-DD/observations/swob-ml/partners/bc-forestry/20230707/1083/2023-07-07-0800-bc-wmb-1083-AUTO-swob.xml',
        'https://hpfx.collab.science.gc.ca/20230707/WXO-DD/observations/swob-ml/partners/bc-forestry/20230707/131/2023-07-07-0000-bc-wmb-131-AUTO-swob.xml',
        'https://hpfx.collab.science.gc.ca/20230707/WXO-DD/observations/swob-ml/partners/bc-forestry/20230707/866/2023-07-07-2000-bc-wmb-866-AUTO-swob.xml'
    ])
def test_file_getter(file_url, remote_ostore_syncer):
    rs = remote_ostore_syncer
    LOGGER.debug(f"file_urls: {file_url}")

    file_path = os.path.join(os.path.dirname(__file__), os.path.basename(file_url))
    assert not os.path.exists(file_path)
    rs._get_file(local_path_file=file_path, file_url=file_url)
    assert os.path.exists(file_path)
    os.unlink(file_path)

def test_file_ostore(remote_ostore_syncer):
    url_log = logging.getLogger('urllib3')
    url_log.setLevel(logging.INFO)

    file_list = remote_ostore_syncer.get_ostore_files()
    LOGGER.debug(f"file_list: {file_list}")


    remote_ostore_syncer.config.ostore_dir = 'cmc'
    cmc_files = remote_ostore_syncer.get_ostore_files()
    LOGGER.debug(f"cmc_files: {remote_ostore_syncer.ostore_files}")