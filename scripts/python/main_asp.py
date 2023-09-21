"""

Summarize what the ASP_daily_climate.R is doing:

A) calculates a time for today, and yesterday
B) calculates a time for 07:00 and 15:00
C) calculates time string for yesterday at 7am to today at 7am
   Tmin - is today at 15:00
D) filters out records for between 7am yesterday and 7am today (PC)
E) filters out records for between 7am yesterday and 15:00 today ()

inputs are: PC.csv, TA,csv, SD.csv, SW.csv
outputs are:
    * E:/Shared/Real-time_Data/ASP_daily_R/ASP_daily-<date>.csv
      - cols: site	DATE	MAXT	MINT	PC	SW
    * E:/Shared/Real-time_Data/ASP_daily_R/ASP_daily-<date>_yesterday.csv
      - cols: site	DATE	MINT_yesterday
    * E:/Shared/Real-time_Data/ASP_daily/ASP_daily-<date>.csv
      - cols: site	DATE	MAXT	MINT	PC	SW

rain delta is the rain at 7am previous day - rain at 7am current day
snow looks like it is whaterver the value was at 7am current day

Comparison between R script output and python script output:

* looking at the date: 2023-09-06

    * R script does not include the actual end date when it calculates the
      min time, even though the logic says:
        Ttemp<-TA %>%
            filter(.,datetime>PC_endtime) %>%
            filter(.,datetime<=Tmin_endtime)

      the python script will include the temperature_end time in its calculation
      of the min temperature.  This means that the min temperatures will be
      calculated differently between R code and python code.

    * missing stations.  The R script doesn't seem to include all the stations for
      every day.  Python date should include all the stations for the specific day
      if they are have values in any of the 4 source files (TA, SW, Etc...)

* temperatures - If a station is missing a temperature values then the
                 R script seems to calculate the temperature as non data
                 or 99999 even when there are 2 or more values for the time
                 window.  This case doesn't show up for the most recent calculations
                 for 2023-09-06.

                 See 1A19P for example. for 2023-09-05

* temperatures - Look at station 1B08P, for the time>yesterday@7:00 and
                 time <=today@15:00 the min temp should be:

"""

import pandas as pd
import datetime
import os
import logging.config
import logging
import remote_ostore_sync
import sys # NOQA

LOGGER = logging.getLogger(__name__)


class main:
    """ties everything together into a simple run method that can be called.
    """

    def __init__(self, date_to_process=None):
        self.config = Config(date_to_process=date_to_process)
        self.ostore_confg = remote_ostore_sync.SyncRemoteConfig(
            remote_date_fmt='%Y%m%d',
            remote_location=self.config.src_url,
            ostore_data_dir='ASP/raw',
            ostore_dir_date_fmt='%Y%m%d',
            local_file_path=self.config.get_local_raw_dir(),
            local_file_date_fmt='%Y%m%d',
            current_date=self.config.current_date
        )

        self.ostore_confg.add_file_filter(self.config.file_list)
        sync = remote_ostore_sync.SyncRemote(self.ostore_confg)
        sync.sync()
        LOGGER.debug("sync process complete")

    def run(self):
        """downloads the data from the ministry of environment website, then processes
        it ultimately dumping the data to a csv file."""
        self.process_data = ProcessASPData(self.config)
        self.process_data.process()

    def syncProcessedData(self):
        """Syncs the data that has been created by this script to object storage"""
        # output_dir is the directory where the processed / transformed data is placed
        local_dir = self.config.get_local_prepd_dir()
        LOGGER.debug(f"local_dir for processed data: {local_dir}")

        obj_dir = self.config.get_object_store_prepd_dir()
        LOGGER.debug(f"local_dir for processed data: {obj_dir}")

        sync = remote_ostore_sync.PushProcessed(src_dir=local_dir, ostore_dir=obj_dir)
        sync.sync()


class Config:
    """describes the configuration that is used to process the automated snow pillow
    data.  Each set of parameters is preceded with a comment describing what that
    parameter will effect in the analysis.

    Environment variables that can be used to override the default values are:
        * ASP_ENV_DATA_DIR: the local directory path where the raw data downloaded from
            the ministry of environment web site will be stored.  Local copies are
            necessary in order to process the data.
        * ASP_PREPD_DATA_DIR: the local directory path where the processed data that
            has been derived from the raw data is stored.
        * ASP_OSTORE_RAW_DATA_DIR: the object storage directory path where the raw asp
            data will be stored.
        * ASP_OSTORE_PREPD_DATA_DIR: the object storage directory path where the
            processed data will be stored.

        Object storage env vars: These are used to enable communication with object
        storage:
        * OBJ_STORE_BUCKET: the name of the object storage bucket
        * OBJ_STORE_SECRET: the secret key for the object storage bucket
        * OBJ_STORE_USER: the user name / client id for the object storage bucket
        * OBJ_STORE_HOST: the host name where the object storage service is

    """

    def __init__(self, date_to_process=None):
        # this source url where the various files described in the parameter
        # self.file_list will be downloaded from
        self.src_url = "https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/"
        self.file_list = ["TA.csv", "PC.csv", "SD.csv", "SW.csv"]

        # the directory where the raw data that gets pulled from the web site will be
        # stored
        self.env_file_raw = os.getenv("ASP_ENV_DATA_DIR", "./data/asp_env")
        # the directory where the processed data will be stored
        self.env_file_prepd = os.getenv("ASP_PREPD_DATA_DIR", "./data/asp_prepd")

        self.ostore_raw_dir = os.getenv("ASP_OSTORE_RAW_DATA_DIR", "ASP/raw")
        self.ostore_prepd_dir = os.getenv("ASP_OSTORE_PREPD_DATA_DIR", "ASP/prepd")

        # the input column from the original data (TA.csv, SW.csv etc) that contains
        # the date times for the various observations.
        self.date_col = "DATE(UTC)"

        # the name of the column in the output data that will contain the date
        self.date_col_name = "DATE"

        # calculate the current date and yesterday's date
        self.current_date = date_to_process
        if self.current_date is None:
            self.current_date = datetime.datetime.now()
        # TODO: put in a type check here to make sure a datetime object was passed
        self.yesterday_date = self.current_date - datetime.timedelta(days=1)

        # the dateformat that will be used to format the date string in the output
        # file paths for the data.
        self.date_format = "%Y%m%d"

        # the name of the column that contains the climate station names in the ouput
        # data
        self.site_col_name = "SITE"

        # the column name that will contain the cumulative precipitation data
        # ie the rain from yesterday at 7am to today at 7am
        self.precip_col_name = "PC"

        # the column name for the snow water equivalent in mm at 7am today
        self.snow_col_name = "SW"

        # the min and max temperature column names that will be used in the output file
        # to store the min and max temperature values.  The date ranges for how these
        # temperatures are calculated are not the same.  They are defined in the
        # parameters:
        #   - temperature_max_start_time
        #   - temperature_max_end_time
        #   - temperature_min_start_time
        #   - temperature_min_end_time
        self.temp_min_col_name = "MINT"
        self.temp_max_col_name = "MAXT"
        self.temp_min_yesterday_col_name = "MINT_yesterday"

        # the value that will be used to replace NaN values in the output file
        self.nan_value = 99999

        # overwriting the default start time in the start dates for today and yesterday
        # this parameter is used to calculate:
        #  - precipitation
        #  - snow water equivalent
        self.default_start_time = self.yesterday_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        self.default_end_time = self.current_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )

        # the time window that will be used to calculate the max temperature
        self.temperature_max_start_time = self.yesterday_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        self.temperature_max_end_time = self.current_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )

        # --------------------------------------------------------------------
        # the time window that will be used to caluculate the min temperature
        self.temperature_min_start_time = self.current_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        self.temperature_min_end_time = self.current_date.replace(
            hour=15, minute=0, second=0, microsecond=0
        )

        # the time window that will be used to calculate the min temperature for
        # yesterday
        self.temperature_min_start_time_yesterday = self.yesterday_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        self.temperature_min_end_time_yesterday = self.current_date.replace(
            hour=7, minute=0, second=0, microsecond=0
        )

    def get_local_raw_dir(self):
        """returns the local directory where the data will be stored, that has
        originated from the ministry of environment web site.  This is the directory
        where the data will be stored before it is processed.

        the data returned includes the datestamp of the data

        :return: local directory of the original data downloaded from the env web site
        :rtype: str
        """
        date_str = self.get_current_date_str()
        local_dir = os.path.join(self.env_file_raw, date_str)
        LOGGER.debug(f"local_dir for raw data: {local_dir}")
        return local_dir

    def get_local_prepd_dir(self):
        """returns the path to the local directory where the processed data will be
        stored.

        the data returned includes the datestamp of the data

        :return: path to the local directory where transformed/processed data will be
            stored
        :rtype: str
        """
        date_str = self.get_current_date_str()
        local_dir = os.path.join(self.env_file_prepd, date_str)
        LOGGER.debug(f"local_dir for processed data: {local_dir}")
        return local_dir

    def get_output_file(self, yesterday=False):
        """calculates the output path for the ASP data based on the current date.

        :return: the file path where the output file will be stored
        :rtype: str
        """
        date_str = self.get_current_date_str()
        date_str_hiphen = self.get_current_date_str("%Y-%m-%d")
        if yesterday:
            output_file_name = f"ASP_daily-{date_str_hiphen}_yesterday.csv"
        else:
            output_file_name = f"ASP_daily-{date_str_hiphen}.csv"
        output_file = os.path.join(self.env_file_prepd, date_str, output_file_name)
        return output_file

    def get_current_date_str(self, date_format=None):
        """takes the current date that was calculated when the object was
        instantiated and returns it as a string based on the string format described
        in the property date_format

        :param date_format: the date format to use, defaults to None in which case it
            will use the default date format defined in self.date_format

        :return: date string using the file format supplied
        :rtype: str
        """
        if not date_format:
            date_format = self.date_format
        return self.current_date.strftime(date_format)

    def get_object_store_prepd_dir(self, date_format=None):
        """
        gets the path in object storage where the prepared / transformed data should
        be copied to.  Takes the parameter ostore_prepd_dir and adds a date string to
        it using the property date_format to format the date in
        """
        date_str = self.get_current_date_str(date_format)
        ostore_dir = os.path.join(self.ostore_prepd_dir, date_str)
        LOGGER.debug(f"ostore_dir: {ostore_dir}")
        return ostore_dir


class ProcessASPData:
    """contains the code / logic that is used to calculate the min / max temperatures,
    the precipitation and the snow water equivalent for the automated snow pillow data.
    """
    def __init__(self, config: Config):
        """recieves the config object that includes a bunch of parameters that can be
        used to control how the various statistics are calculated.

        :param config: a config object that contains the parameters that will be used
        :type config: Config
        """
        self.config = config

    def process(self):
        """processes all the data, ie the temperature / precipitation / snow water data
        then combines the dataframes into a single data frame by joining based on the
        site id, and finally dumps the data to a csv file.
        """
        output_file_name = self.config.get_output_file()
        output_file_name_yesterday = self.config.get_output_file(yesterday=True)
        output_dir_name = os.path.dirname(output_file_name)
        if not os.path.exists(output_dir_name):
            os.makedirs(output_dir_name)
        LOGGER.debug(f"output_dir_name: {output_dir_name}")

        if not os.path.exists(output_file_name):
            temp_df = self.process_TA()
            precip_df = self.process_PC()
            snoww_df = self.process_SW()
            # finally join together and dump to csv
            # todo:
            #   * do the actual join
            #   * define the output path in the config object
            #   * add logic to only proceed if the out file doesn't exist
            #   *
            temp_precip_df = pd.merge(
                temp_df, precip_df, how="outer", on=[self.config.site_col_name]
            )
            temp_precip_snow_df = pd.merge(
                temp_precip_df, snoww_df, how="outer", on=[self.config.site_col_name]
            )
            temp_precip_snow_df = temp_precip_snow_df.sort_values(
                [self.config.site_col_name]
            )

            # re-order the columns
            temp_precip_snow_df = temp_precip_snow_df[
                [
                    self.config.site_col_name,
                    self.config.date_col_name,
                    self.config.temp_max_col_name,
                    self.config.temp_min_col_name,
                    self.config.precip_col_name,
                    self.config.snow_col_name,
                ]
            ]

            # replace NaN with 99999 or the config.nodata_value
            temp_precip_snow_df[
                self.config.date_col_name
            ] = self.config.default_end_time

            print(temp_precip_snow_df.head(28))

            # dump the final data frame with all the stats required for today to a csv
            # file
            temp_precip_snow_df.to_csv(
                output_file_name,
                encoding="utf-8",
                index=False,
                na_rep=self.config.nan_value,
            )

        if not os.path.exists(output_file_name_yesterday):
            temp_yesterday_df = self.process_TA_yesterday()
            temp_yesterday_df.to_csv(
                output_file_name_yesterday,
                encoding="utf-8",
                index=False,
                na_rep=self.config.nan_value
            )

    def extract_site_id(self, site_name):
        """extracts the site id from the site name, which is the first word in the
        site name

        :param site_name: site name
        :type site_name: string
        :return: site id
        :rtype: string
        """
        return site_name.split(" ")[0]

    def process_PC(self):
        """process the PC.csv file which contains the precipitation data from the ASP
        stations.  The precipitation data is cumulative, so the precipitation is
        calculated by subtracting the value for the previous day at 7am from the current
        day at 7am

        :return: a pandas dataframe with the columns (SITE, PC)
        :rtype: pd.df
        """
        local_dir = self.config.get_local_raw_dir()
        local_file = os.path.join(local_dir, "PC.csv")

        # read the csv into a dataframe
        df_pc = pd.read_csv(
            local_file, parse_dates=[self.config.date_col], encoding="ISO-8859-1"
        )

        # rename the date column, mostly to take out the '(' and ')' characters that
        df_pc = df_pc.rename(columns={self.config.date_col: self.config.date_col_name})

        # filter for records that are for 7am yesterday and 7am today, based on default
        # times defined in config object
        df_pc_date_filter = df_pc.query(
            f"{self.config.date_col_name} == @self.config.default_start_time or "
            + f"{self.config.date_col_name} ==  @self.config.default_end_time"
        )

        # pivot the columns into rows for the various stations
        df_pc_format = df_pc_date_filter.melt(
            id_vars=[self.config.date_col_name],
            var_name=self.config.site_col_name,
            value_name="precipitation",
        )

        # concat the values in the climate station column (default value 'site')
        # column to only include site id and remove the full name for the climate
        # station
        df_pc_format[self.config.site_col_name] = df_pc_format[
            self.config.site_col_name
        ].apply(self.extract_site_id)

        # sort the values so we can get rid of the NaN values
        df_pc_format[self.config.precip_col_name] = (
            df_pc_format.sort_values(
                [self.config.date_col_name, self.config.site_col_name]
            )
            .groupby(self.config.site_col_name)["precipitation"]
            .diff()
        )
        df_precip_accum = (
            df_pc_format.groupby([self.config.site_col_name])
            .agg({self.config.precip_col_name: "max"})
            .reset_index()
        )
        print(df_precip_accum)
        return df_precip_accum

    def _process_TA(self, start_time, end_time, summary_function, summary_col_name):
        """temperature data get processed the same way for different output values.

        """
        local_dir = self.config.get_local_raw_dir()
        local_file = os.path.join(local_dir, "TA.csv")
        LOGGER.debug(f"local file: {local_file}")

        # read the csv to a dataframe
        df = pd.read_csv(
            local_file, parse_dates=[self.config.date_col], encoding="ISO-8859-1"
        )

        # rename the date column, mostly to take out the '(' and ')' characters that
        # make it tricky to work with
        df = df.rename(columns={self.config.date_col: self.config.date_col_name})

        # filter out records between yesterday based on config TA_start_time and
        #   TA_end_time properties
        df_date_filter = df.query(
            f"{self.config.date_col_name} > @start_time"
            + f" and {self.config.date_col_name} <= " +
            "@end_time"
        )

        # pivot the columns into rows for the different stations for the min and max
        # temperature data frames
        df_format = df_date_filter.melt(
            id_vars=[self.config.date_col_name],
            var_name=self.config.site_col_name,
            value_name="temperature"
        )

        # truncate the climate station column values to only include the stations id
        df_format[self.config.site_col_name] = df_format[
            self.config.site_col_name
        ].apply(self.extract_site_id)

        # summarize, getting the min and the max temperature for the different data
        # frames.  Not sure why but the start / end for min and max are different.
        df_calcd = (
            df_format.groupby(self.config.site_col_name)["temperature"]
            .agg([(summary_col_name, summary_function)])
            .reset_index()
        )

        return df_calcd

    def process_TA(self):
        # start_time, end_time, summary_function
        df_max_t = self._process_TA(start_time=self.config.temperature_max_start_time,
                                    end_time=self.config.temperature_max_end_time,
                                    summary_function="max",
                                    summary_col_name=self.config.temp_max_col_name)

        df_min_t = self._process_TA(start_time=self.config.temperature_min_start_time,
                                    end_time=self.config.temperature_min_end_time,
                                    summary_function="min",
                                    summary_col_name=self.config.temp_min_col_name)
        print(df_max_t)
        # join the min / max data frames together using site_col_name
        temp_min_max_df = pd.merge(
            df_max_t, df_min_t, how="outer", on=[self.config.site_col_name]
        )

        # finally add the date column back into the table
        temp_min_max_df.insert(
            1, self.config.date_col_name, self.config.default_end_time
        )

        print(temp_min_max_df)
        return temp_min_max_df

    def process_TA_yesterday(self):
        """calculates the dataframe that contains the min temperature for yesterday.

        :return: dataframe with the min temperature for yesterday, columns:
            - site
            - date
            - mint_yesterday
        :rtype: pd.df
        """
        df_min_yesterday = self._process_TA(
            start_time=self.config.temperature_min_start_time_yesterday,
            end_time=self.config.temperature_min_end_time_yesterday,
            summary_function="min",
            summary_col_name=self.config.temp_min_yesterday_col_name)

        df_min_yesterday.insert(
            1, self.config.date_col_name,
            self.config.temperature_min_start_time_yesterday
        )
        print(df_min_yesterday)
        return df_min_yesterday

    def process_SW(self):
        """get the snow water data... Just retrieves the value for 7am
        for the current date.
        """
        local_dir = self.config.get_local_raw_dir()
        local_file = os.path.join(local_dir, "SW.csv")
        LOGGER.debug(f"local file: {local_file}")

        # read the csv to a dataframe
        df = pd.read_csv(
            local_file, parse_dates=[self.config.date_col], encoding="ISO-8859-1"
        )
        # rename the date column, mostly to take out the '(' and ')' characters that
        # make it tricky to work with
        df = df.rename(columns={self.config.date_col: self.config.date_col_name})

        # filter out records to only include for today at 7am
        df_date_filter = df.query(
            f"{self.config.date_col_name} == @self.config.default_end_time"
        )

        print(df_date_filter)
        df_format = df_date_filter.melt(
            id_vars=[self.config.date_col_name],
            var_name=self.config.site_col_name,
            value_name=self.config.snow_col_name,
        )
        df_format[self.config.site_col_name] = df_format[
            self.config.site_col_name
        ].apply(self.extract_site_id)
        print(df_format.head(25))
        df_format = df_format.drop(self.config.date_col_name, axis=1)

        # drop the date column
        return df_format


if __name__ == "__main__":
    # log config
    log_config_path = os.path.join(os.path.dirname(__file__), "logging.config")
    logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
    LOGGER = logging.getLogger(__name__)
    LOGGER.info(f"starting {__name__}")

    # override config to debug
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.debug(f"logging level set to {LOGGER.level}")

    # be default will run the current date.  If you want to run a different date
    # populate the date_to_process parameter in the main constructor with
    # datetime object
    # example:
    #     date_to_process = datetime.datetime.strptime('20230710', '%Y%m%d')
    #     main = main(date_to_process=date_to_process)
    #date_to_process = datetime.datetime.strptime('20230920', '%Y%m%d')
    #main = main(date_to_process=date_to_process)

    main = main()
    main.run()
    main.syncProcessedData()
