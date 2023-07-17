

import NRUtil.NRObjStoreUtil
import requests
import logging
import bs4
import os
import multiprocessing
import time


LOGGER = logging.getLogger(__name__)
OSTORE = NRUtil.NRObjStoreUtil.ObjectStoreUtil()


def get_file(local_path_file, file_url, ostore_path, sleep=2):
    """_summary_

    :param local_path_file: _description_
    :type local_path_file: _type_
    :param file_url: _description_
    :type file_url: _type_
    """
    if not os.path.exists(local_path_file):
        LOGGER.debug(f"local_path_file: {local_path_file}")
        LOGGER.debug(f"file_url: {file_url}")
        session = requests.Session()
        try:
            r = session.get(file_url)
        except requests.exceptions.ConnectionError as e:
            LOGGER.error(f"ConnectionError: {e}")
            time.sleep(sleep)
            session.close()
            get_file(local_path_file, file_url, ostore_path, sleep=sleep+10)
        else:
            #r = requests.get(file_url)
            with open(local_path_file, 'wb') as f:
                f.write(r.content)
            session.close()
    # if the file already exists locally then just write to ostore.  Shouldn't
    # get here if it already exists in ostore.
    LOGGER.debug(f"ostore path: {ostore_path}")
    OSTORE.put_object(local_path=local_path_file, ostore_path=ostore_path)

def pull_s3_file(local_path_file, ostore_path):
    LOGGER.debug(f"local_path_file: {local_path_file}")
    LOGGER.debug(f"ostore_path: {ostore_path}")
    OSTORE.get_object(local_path=local_path_file, file_path=ostore_path)


class SyncRemoteConfig:
    def __init__(self,
                 remote_location,
                 ostore_dir,
                 remote_date_fmt,
                 ostore_dir_date_fmt,
                 current_date
                 ):
        self.remote_location = remote_location
        self.ostore_dir = ostore_dir
        self.remote_date_fmt = remote_date_fmt
        self.ostore_dir_date_fmt = ostore_dir_date_fmt
        self.current_date = current_date
        self.ostore_dir = self.calc_ostore_path()

    def calc_root_url(self):
        """Fills in the date strings in the url template to create a valid url
        based on the date contained in the property current_date

        :return: url
        :rtype: str
        """
        date_str = self.current_date.strftime(self.remote_date_fmt)
        LOGGER.debug(f"date_str: {date_str}")
        url = self.remote_location.format(date_str=date_str)
        LOGGER.debug(f"url: {url}")
        return url

    def calc_ostore_path(self):
        date_str = self.current_date.strftime(self.ostore_dir_date_fmt)
        ostore_path = self.ostore_dir.format(date_str=date_str)
        LOGGER.debug(f"ostore_path: {ostore_path}")
        return ostore_path


class Contents:
    """use to wrap the results of the html parser
    """
    def __init__(self, directories, files):
        self.directories = directories
        self.files = files

class SyncRemote:
    """expecting the following environment variables to be set:
    OBJ_STORE_BUCKET
    OBJ_STORE_SECRET
    OBJ_STORE_USER
    OBJ_STORE_HOST
    """

    def __init__(self, config: SyncRemoteConfig):
        self.config = config

        # these are some of the directories defined in the returned html that should
        # not be inluded when querying the html page for directories
        skip_dirs = ['name', 'Last modified', 'Size', 'Description', 'Parent Directory']
        self.skip_dirs = [dir.lower() for dir in skip_dirs]

        # will get populated with the data that needs to be downloaded, and then passed
        # to an async queue for downloading
        self.dl_job_list = []
        self.ostore_files = []
        self.ostore_pull_job_list = []

    def sync(self, url: str, local_file_path: str, ostore_path, first_call=True, recurse_depth=0):
        """using the config that was sent will read the data that is available on
        the remote url, and the data that currently exists in object storage, then
        iterate over the remote data, pulling and pushing to object storage as needed.

        :param url: input url that should be synced (assumes this is a hpfx url)
        :type url: str
        :param local_file_path: The path where the files should be syned to
        :type local_file_path: str
        :param stop: Used for debugging... if set to true will raise an exception after
            a single directory has been synced
        :type stop: bool, optional
        """
        # TODO: add a validation check to make sure the url is to the federal government
        #       as other url's will likley not work due to differently formatted html
        #       describing the file contents
        #
        LOGGER.debug(f"recurse_depth: {recurse_depth}")
        recurse_depth += 1
        if first_call:
            self.get_ostore_files()

        contents = self._get_contents(url)
        for infile in contents.files:
            # doesn't exist in ostore
            ostore_full_path = os.path.join(ostore_path, infile)
            local_path_file = os.path.join(local_file_path, infile)
            local_path_dir = os.path.dirname(local_path_file)
            file_url = os.path.join(url, infile)

            if ostore_full_path not in self.ostore_files:
                if not os.path.exists(local_path_file):
                    # file doesn't exist in ostore or locally
                    if not os.path.exists(local_path_dir):
                        os.makedirs(local_path_dir)

                    LOGGER.debug(f"ostore_full_path: {ostore_full_path}")
                    LOGGER.debug(f"adding local_path_file: {local_path_file}")
                    self.dl_job_list.append((local_path_file, file_url,
                                            ostore_full_path))
            elif not os.path.exists(local_path_file):
                # file IS in ostore but isn't available locally
                LOGGER.debug(f"pulling from ostore path to local: {ostore_full_path}")
                self.ostore_pull_job_list.append((local_path_file, ostore_full_path))

        for dir in contents.directories:
            dir_url = os.path.join(url, dir)
            next_file_path = os.path.join(local_file_path, dir)
            ostore_path_dir = os.path.join(ostore_path, dir)
            LOGGER.debug(f"dir: {dir_url}")
            self.sync(url=dir_url, local_file_path=next_file_path,
                      ostore_path=ostore_path_dir, first_call=False,
                      recurse_depth=recurse_depth)

        if first_call:
            LOGGER.debug(f"FIRST CALL: {len(self.dl_job_list)}")
            LOGGER.debug(f"self.dl_job_list: {self.dl_job_list}")
            try:
                if self.dl_job_list:
                    with multiprocessing.Pool(processes=6) as p:
                        #p.map(self._get_file, self.dl_job_list)
                        p.starmap(get_file, self.dl_job_list)

                LOGGER.debug(f"ostore pulll job list: {self.ostore_pull_job_list}")
                if self.ostore_pull_job_list:
                    with multiprocessing.Pool(processes=6) as p:
                        #p.map(self._get_file, self.dl_job_list)

                        p.starmap(pull_s3_file, self.ostore_pull_job_list)

            except KeyboardInterrupt:
                LOGGER.error('keyboard interupt... Exiting download pool')
            LOGGER.debug(f"FINISHED: {len(self.dl_job_list)}")

    def _get_contents(self, url) -> Contents:
        """Reads the html from the url and parses it to try the contents as links to
        either directories or files.

        :param url: _description_
        :type url: _type_
        :return: _description_
        :rtype: _type_
        """
        r = requests.get(url)
        html = r.text
        contents = self._parse_html(html=html)
        return contents

    def _parse_html(self, html:str) -> dict:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        # hrefs = soup.find_all('a')
        # #LOGGER.debug(f'{soup}')
        # dirs = []
        # for href in hrefs:
        #     if href.text.lower() not in self.skip_dirs:
        #         LOGGER.debug(f'hrefs: {href["href"]}')
        #         dirs.append(href['href'])
        directories = []
        files = []
        for img_tag, a_tag in zip(soup.find_all('img'), soup.find_all('a')):
            if a_tag.text.lower() not in self.skip_dirs:
                if img_tag['alt'] == '[DIR]':
                    directories.append(a_tag['href'])
                elif img_tag['alt'].strip() not in ['Icon', '[PARENTDIR]']:
                    files.append(a_tag['href'])
        LOGGER.debug(f"files: {files}")
        LOGGER.debug(f"dirs: {directories}")
        contents = Contents(directories=directories, files=files)
        return contents

    def get_ostore_files(self):
        if self.config.ostore_dir[-1] != '/':
            self.config.ostore_dir += '/'

        file_list = OSTORE.list_objects(self.config.ostore_dir, return_file_names_only=True)
        file_list = [i for i in file_list]

        LOGGER.debug(f"file_list: {file_list}")
        self.ostore_files = file_list

