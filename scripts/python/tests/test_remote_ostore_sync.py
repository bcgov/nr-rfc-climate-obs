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
        'https://hpfx.collab.science.gc.ca/20230816/WXO-DD/observations/swob-ml/partners/bc-forestry/20230816/1083/2023-08-16-0800-bc-wmb-1083-AUTO-swob.xml',
        'https://hpfx.collab.science.gc.ca/20230816/WXO-DD/observations/swob-ml/partners/bc-forestry/20230816/131/2023-08-16-0000-bc-wmb-131-AUTO-swob.xml',
        'https://hpfx.collab.science.gc.ca/20230816/WXO-DD/observations/swob-ml/partners/bc-forestry/20230816/866/2023-08-16-2000-bc-wmb-866-AUTO-swob.xml'
    ])
def test_file_getter(file_url, remote_ostore_syncer):
    rs = remote_ostore_syncer
    LOGGER.debug(f"file_url: {file_url}")

    ostore_path = os.path.join(rs.config.ostore_dir, os.path.basename(file_url))

    file_path = os.path.join(os.path.dirname(__file__), os.path.basename(file_url))
    assert not os.path.exists(file_path)
    remote_ostore_sync.get_file(local_path_file=file_path, file_url=file_url, ostore_path=ostore_path)
    assert os.path.exists(file_path)
    os.unlink(file_path)

def test_file_ostore(remote_ostore_syncer):
    url_log = logging.getLogger('urllib3')
    url_log.setLevel(logging.INFO)
    remote_ostore_syncer.config.ostore_dir = 'F_WX/raw/20230816'
    LOGGER.debug(f"ostore directory: {remote_ostore_syncer.config.ostore_dir}")
    file_list = remote_ostore_syncer.get_ostore_files()
    LOGGER.debug(f"number of files retrieved: {len(list(file_list))}")
    LOGGER.debug(f"first 10 files in file_list: {file_list[:10]}")


    remote_ostore_syncer.config.ostore_dir = 'cmc'
    LOGGER.debug(f"ostore directory: {remote_ostore_syncer.config.ostore_dir}")
    cmc_files = remote_ostore_syncer.get_ostore_files()
    LOGGER.debug(f"number of cmc files read cmc_files: {len(list(cmc_files))}")
    LOGGER.debug(f"first 10 cmc_files files : {remote_ostore_syncer.ostore_files[:10]}")


def test_SyncProcessed(remote_ostore2way_sync):
    sync = remote_ostore2way_sync
    LOGGER.debug("got here")
    LOGGER.debug(f"remote_ostore2way_sync: {remote_ostore2way_sync}")

    local_files = sync.get_local_files()
    LOGGER.debug(f"local_files: {local_files}")


    #remote_ostore2way_sync.sync()

def test_get_local_files(remote_ostore2way_sync):
    """_summary_

    :param remote_ostore2way_sync: _description_
    :type remote_ostore2way_sync: _type_
    """
    sync = remote_ostore2way_sync
    ostore_files = sync.get_ostore_files()
    LOGGER.debug(f"ostore_files: {ostore_files}")

    # now add a single file
    ## create a temp file
    test_file_name = 'test_file.txt'
    with open(test_file_name, "w") as f:
        f.write("test file\n")

    ostore_path = os.path.join(sync.ostore_dir, test_file_name)
    remote_ostore_sync.OSTORE.put_object(ostore_path=ostore_path,
                                         local_path=test_file_name)

    sync = remote_ostore2way_sync
    ostore_files = sync.get_ostore_files()
    LOGGER.debug(f"ostore_files: {ostore_files}")
    assert ostore_path in ostore_files

    # test cleanup, delete the ostore file and delete the local file
    remote_ostore_sync.OSTORE.delete_remote_file(dest_file=ostore_path)
    if os.path.exists(test_file_name):
        os.remove(test_file_name)

def test_two_way_sync(remote_ostore2way_sync):
    sync = remote_ostore2way_sync

    test_file_name = 'test_file.txt'
    with open(test_file_name, "w") as f:
        f.write("test file\n")

    LOGGER.debug(f"syncdir: {sync.src_dir}")

    sync.sync()

