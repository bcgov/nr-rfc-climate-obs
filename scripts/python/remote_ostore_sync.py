"""
This module was created to sync data from a remote location to
local storage and then to object storage.

"""

import NRUtil.NRObjStoreUtil
import requests
import logging
import bs4
import os
import multiprocessing
import time
import datetime


LOGGER = logging.getLogger(__name__)
OSTORE = NRUtil.NRObjStoreUtil.ObjectStoreUtil()


def get_file(local_path_file, file_url, ostore_path, sleep=2):
    """This method gets called asyncronously

    :param local_path_file: The local file path where the file should be saved
    :type local_path_file: str
    :param file_url: the remote url where the file can be downloaded from
    :type file_url: str
    :param ostore_path: the object store path, basically where the files should be
        located when copied to object storage
    :type ostore_path: str
    :param sleep: The number of seconds to sleep before retrying the download, mostly
        used when a connection error occurs, the method will recurse and sleep for
        this amount of time before retrying
    :type sleep: int, optional
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
    """This method gets called asyncronously from other methods in this module.  It
    is required to download s3 data to a local path.

    :param local_path_file: The local path where the S3 data should get copied to
    :type local_path_file: str
    :param ostore_path: the object store path where the file is comming from
    :type ostore_path: str
    """
    LOGGER.debug(f"local_path_file: {local_path_file}")
    LOGGER.debug(f"ostore_path: {ostore_path}")
    OSTORE.get_object(local_path=local_path_file, file_path=ostore_path)

def push_s3_file(local_path_file, ostore_path):
    """This method gets called asyncronously from other methods in this module.  It
    is required to upload data to s3.

    :param local_path_file: The local path where the data is located
    :type local_path_file: str
    :param ostore_path: the object store path where the file should be copied to
    :type ostore_path: str
    """
    LOGGER.debug(f"local_path_file: {local_path_file}")
    LOGGER.debug(f"ostore_path: {ostore_path}")
    OSTORE.put_object(local_path=local_path_file, ostore_path=ostore_path)

class SyncRemoteConfig:
    """this class is a standard config class that is used to describe how data
    should be synced between the remote source, local paths, and object storage.
    """
    def __init__(self,
                 remote_location: str,
                 remote_date_fmt: str,
                 ostore_data_dir: str,
                 ostore_dir_date_fmt: str,
                 local_file_path: str,
                 local_file_date_fmt: str,
                 current_date: datetime.datetime
                 ):
        """constructor defining the configuration for a data sync

        :param remote_location: the source location where data should originate from
          this path can contain the following f string variables: date_str
        :type remote_location: str(url)
        :param ostore_dir: the object store path where the data should be copied to,
            this path can contain the following f string variables: date_str
        :type ostore_dir: str
        :param remote_date_fmt: the date format that should be used to fill in the
            date_str variable in the remote_location
        :type remote_date_fmt: str
        :param ostore_dir_date_fmt: if the object store path contains date_str the
            format that for that date string
        :type ostore_dir_date_fmt: str
        :param local_file_path: The local file path where the data should be copied
        :type local_file_path: When resolving the path the date format that should be
            used to fill in the date_str variable
        :param current_date: the date object that should be used to calculate the
            date strings
        :type current_date: datetime.datetime
        """
        self.remote_location = remote_location
        self.ostore_data_dir = ostore_data_dir
        self.remote_date_fmt = remote_date_fmt
        self.ostore_dir_date_fmt = ostore_dir_date_fmt
        self.local_file_path = local_file_path
        self.local_file_date_fmt = local_file_date_fmt
        self.current_date = current_date
        self.yesterday = self.current_date - datetime.timedelta(days=1)
        self.ostore_dir = self.calc_ostore_path()
        # self.yesterday_date_str = self.yesterday.strftime(self.remote_date_fmt)
        self.max_retries = 5
        LOGGER.debug(f"self.local_file_date_fmt: {self.local_file_date_fmt}")
        self.file_filter = []
        self.check_local_dirs()

    def check_local_dirs(self):
        """Checks to see if the output path for the local data exists
        """
        local_file_path = self.calc_local_path()
        if not os.path.exists(local_file_path):
            LOGGER.info(
                f"creating the ouput path for the local data: {local_file_path}")
            os.makedirs(local_file_path)

    def add_file_filter(self, file_filter: list):
        """recieves a list of file names without any path that should be included in
        the sync operation.  If no filter is specified then all files found on the
        remote will be synced.

        if no files are added to the filter, then all the files on the remote site
        will be downloaded.  If a single or multiple files are added to the filter
        then only files matching the names of those in this filter will be downloaded

        :param file_filter: a list of files that should be synced... all others will
            be ignored.  If left empty then all files will be synced.
        :type file_filter: list
        """
        if not isinstance(file_filter, list):
            raise TypeError(f"file_filter must be a list: {file_filter}")
        self.file_filter.extend(file_filter)

    def calc_root_url(self):
        """Fills in the date strings in the url template to create a valid url
        based on the date contained in the property current_date

        :return: the url with the current_date date_str parameter populated
        :rtype: str
        """
        date_str = self.current_date.strftime(self.remote_date_fmt)
        yesterday_date_str = self.yesterday.strftime(self.remote_date_fmt)
        LOGGER.debug(f"date_str: {date_str}")
        url = self.remote_location.format(date_str=date_str,
                                          yesterday_date_str=yesterday_date_str)
        LOGGER.debug(f"url: {url}")
        return url

    def calc_ostore_path(self):
        """Fills in the date strings in the ostore path template to create a valid
        ostore path

        :return: a valid path to object storage based on the date that is contained
            in the property current_date
        :rtype: str
        """
        date_str = self.current_date.strftime(self.ostore_dir_date_fmt)
        ostore_dir = os.path.join(self.ostore_data_dir, date_str)
        LOGGER.debug(f"ostore_path: {ostore_dir}")
        return ostore_dir

    def calc_local_path(self):
        """Takes the local file path that may have date dependencies in it and
        translates those to paths to the local file system

        :return: the local file path with the date_str parameter populated
        :rtype: str
        """
        LOGGER.debug(f"self.current_date {self.current_date}")
        LOGGER.debug(f"self.local_file_date_fmt: {self.local_file_date_fmt}")
        date_str = self.current_date.strftime(self.local_file_date_fmt)
        local_path = self.local_file_path.format(date_str=date_str)
        LOGGER.debug(f"local_path: {local_path}")
        return local_path

class Contents:
    """use to wrap the results of the html parser
    """
    def __init__(self, directories, files):
        self.directories = directories
        self.files = files

class SyncRemote:
    """This class contains the main functionality to do the three way sync between
    ostore / local / remote.  It receives a SyncRemoteConfig object that describes
    what needs to be synced, then calling the sync method will do the work.

    This class requires the following environment variables to be set in order to
    communicate with object storage:

      * OBJ_STORE_BUCKET
      * OBJ_STORE_SECRET
      * OBJ_STORE_USER
      * OBJ_STORE_HOST
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
        self.ostore_push_job_list = []

    def sync(self):
        root_url = self.config.calc_root_url()
        ostore_path = self.config.calc_ostore_path()
        local_file_path = self.config.calc_local_path()
        self._sync(url=root_url,
                   local_file_path=local_file_path,
                   ostore_path=ostore_path,
                   first_call=True
                   )

    def _sync(self, url: str, local_file_path: str, ostore_path, first_call=True, recurse_depth=0):
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
            LOGGER.debug(f"infile: {infile}")
            # apply filter: there is a filter, and the current file is not in it
            if (self.config.file_filter) and (infile not in self.config.file_filter):
                continue


            LOGGER.debug(f"infile: {infile}")
            ostore_full_path = os.path.join(ostore_path, infile)
            local_path_file = os.path.join(local_file_path, infile)
            local_path_dir = os.path.dirname(local_path_file)
            file_url = os.path.join(url, infile)

            # doesn't exist in ostore
            if ostore_full_path not in self.ostore_files:
                # the file doesn't exist in ostore or locally
                if not os.path.exists(local_path_file):
                    # the directory doesn't exist locally
                    if not os.path.exists(local_path_dir):
                        os.makedirs(local_path_dir)

                    LOGGER.debug(f"ostore_full_path: {ostore_full_path}")
                    LOGGER.debug(f"adding local_path_file: {local_path_file}")
                    # add the file to the list of files to pull from the remote
                    self.dl_job_list.append((local_path_file, file_url,
                                            ostore_full_path))
                # file exists locally, but not in ostore
                else:
                    LOGGER.debug(f"file exists locally but not in ostore: {local_path_file}")
                    self.ostore_push_job_list.append((local_path_file, ostore_full_path))

            # Doesn't exist locally, but does exist in ostore
            elif not os.path.exists(local_path_file):
                LOGGER.debug(f"pulling from ostore path to local: {ostore_full_path}")
                self.ostore_pull_job_list.append((local_path_file, ostore_full_path))
            # the file exists locally, but not in ostore
            # elif os.path.exists(local_path_file):
            #     LOGGER.debug(f"file exists locally but not in ostore: {local_path_file}")
            #     self.ostore_push_job_list.append((local_path_file, ostore_full_path))


        for dir in contents.directories:
            dir_url = os.path.join(url, dir)
            next_file_path = os.path.join(local_file_path, dir)
            ostore_path_dir = os.path.join(ostore_path, dir)
            LOGGER.debug(f"dir: {dir_url}")
            self._sync(url=dir_url, local_file_path=next_file_path,
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

                if self.ostore_push_job_list:
                    with multiprocessing.Pool(processes=6) as p:
                        p.starmap(push_s3_file, self.ostore_push_job_list)

            except KeyboardInterrupt:
                LOGGER.error('keyboard interupt... Exiting download pool')
            LOGGER.debug(f"FINISHED: {len(self.dl_job_list)}")

    def _get_contents(self, url, retries=0) -> Contents:
        """Reads the html from the url and parses it to try the contents as links to
        either directories or files.

        :param url: _description_
        :type url: _type_
        :return: _description_
        :rtype: _type_
        """
        r = None
        try:
            r = requests.get(url)
            html = r.text
            contents = self._parse_html(html=html)
            r.close()
            return contents
        except requests.exceptions.ConnectionError:
            if r and isinstance(r, requests.Response):
                r.close()
            if retries > self.config.max_retries:
                raise
            retries += 1
            sleep_time = retries * 5
            LOGGER.error(f"ConnectionError, sleeping for {sleep_time} seconds and retrying: {url}")
            time.sleep(sleep_time)
            contents = self._get_contents(url=url, retries=retries)
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
        a_tags = soup.find_all('a')
        #img_a_tags = zip(soup.find_all('img'), soup.find_all('a'))
        LOGGER.debug(f"img_a_tags: {len(a_tags)}")
        for a_tag in a_tags:
            just_a_tag_text = a_tag.text.lower()
            if just_a_tag_text == 'ObsTephi_12_CYZS.csv'.lower() or \
                just_a_tag_text == 'ObsTephi_12_CZXS.csv'.lower():
                LOGGER.debug(f"just_a_tag_text: {just_a_tag_text}")
            if just_a_tag_text not in self.skip_dirs:
                LOGGER.debug(f"a_tag: {a_tag.text}")
                # id directory by trailing slash in the file name
                if a_tag.text[-1] == '/':
                    directories.append(a_tag.text)
                else:
                    files.append(a_tag.text)
        LOGGER.debug(f"files: {files[:10]}...")
        contents = Contents(directories=directories, files=files)

        return contents

    def get_ostore_files(self):
        LOGGER.info("retrieving list of files from object storage... may take a moment")
        if self.config.ostore_data_dir[-1] != '/':
            self.config.ostore_data_dir += '/'

        file_list = OSTORE.list_objects(self.config.ostore_data_dir, return_file_names_only=True)
        file_list = [i for i in file_list]

        LOGGER.debug(f"first 10 files of {len(list(file_list))} are: {file_list[:10]}")
        self.ostore_files = file_list
        return self.ostore_files

class PushProcessed():
    """This class processes generated data, ie this data does not have a corresponding
    web reference via a url from an website / federal gov data mart.

    as  a result the inputs to this sync are much simpler, ie they only contain two
    input directories.  The one from the remote ostore and the one from the local file
    path
    """

    def __init__(self, src_dir, ostore_dir, ostore_file_filter=[]):
        """constructor

        :param src_dir: the source directory where the data should be copied from
        :type src_dir: str
        :param ostore_dir: the object store directory where the data should be copied
            to
        :type ostore_dir: str

        """
        self.src_dir = os.path.abspath(src_dir)
        self.ostore_dir = ostore_dir

        self.upload_list = []

    def sync(self):
        """main method to sync the data between the local file system and object
        storage
        """

        local_files = self.get_local_files()
        ostore_files = self.get_ostore_files()
        LOGGER.debug(f"local_files: {local_files}")
        LOGGER.debug(f"src dir: {self.src_dir}")

        # iterate through each local_file to determine if it has a corresponding
        # file in ostore
        for local_file in local_files:
            # add the local file path to the src_dir
            LOGGER.debug(f"local_file: {local_file}")
            local_dir = os.path.dirname(local_file)
            relative_dir = os.path.relpath(local_dir, self.src_dir)
            LOGGER.debug(f"relative_dir: {relative_dir}")
            # this is the path to the local file with self.src_dir prefix removed
            relative_file = os.path.join(relative_dir, os.path.basename(local_file))
            LOGGER.debug(f"relative_file: {relative_file}")

            # next calculate the path to the object store file
            ostore_path = os.path.normpath(os.path.join(self.ostore_dir, relative_file))
            LOGGER.debug(f"ostore_path: {ostore_path}")

            if ostore_path not in ostore_files:
                LOGGER.debug(f"ostore_path not in ostore_files: {ostore_path}")
                self.upload_list.append((local_file, ostore_path))

        if self.upload_list:
            with multiprocessing.Pool(processes=6) as p:
                p.starmap(push_s3_file, self.upload_list)



    def get_local_files(self, input_dir=None):
        if input_dir is None:
            input_dir = self.src_dir
        LOGGER.debug(f"input_dir: {input_dir}")
        contents = os.listdir(input_dir)
        files = []
        for content in contents:
            LOGGER.debug(f'content: {content}')
            cont_full_path = os.path.join(input_dir, content)
            if os.path.isdir(cont_full_path):
                files.extend(self.get_local_files(cont_full_path))
            else:
                files.append(cont_full_path)
            LOGGER.debug(f"files: {files}")
        LOGGER.debug(f"files before return: {files}")
        return files

    def get_ostore_files(self, ostore_dir=None):
        """gets a list of files that are currently in object storage for the directory
        ostore_dir.
        """
        if not ostore_dir:
            ostore_dir = self.ostore_dir
        LOGGER.debug(f"ostore_dir pre fix: {ostore_dir} {ostore_dir[-1]}")
        if ostore_dir[-1] != '/':
            ostore_dir += '/'
        LOGGER.debug(f"ostore_dir: {ostore_dir} ")
        ostr_file_list = OSTORE.list_objects(ostore_dir, return_file_names_only=True)
        LOGGER.debug(f"file_list: {ostr_file_list}")
        return ostr_file_list
