"""

Summarize what the ASP_daily_climate.R is doing:

A) calculates a time for today, and yesterday
B) calculates a time for 7:00 and 15:00
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


Looks like it filters for specific date range from 7am to 7am then calculates the
min temp / max temp / rain delta / ??? snow

rain delta is the rain at 7am previous day - rain at 7am current day
snow looks like it is whaterver the value was at 7am current day

Comparison between R script output and python script output:

* temperatures - If a station is missing a temperature values then the
                 R script seems to calculate the temperature as non data
                 or 99999 even when there are 2 or more values for the time
                 window.

                 See 1A19P for example.

* temperatures - Look at station 1B08P, for the time>yesterday@7:00 and
                 time <=today@15:00 the min temp should be:

"""

import pandas as pd
import datetime
import requests
import os
import logging.config
import logging
#import datetime.timedelta

LOGGER = logging.getLogger(__name__)

class main:
    """ties everything together into a simple run method that can be called.
    """

    def __init__(self):
        self.config = Config()
        self.get_data = GetData(self.config)

    def run(self):
        self.get_data.get_data()
        self.process_data = ProcessASPData(self.config)
        self.process_data.process()

class Config:
    """describes the configuration for the ASP data processing.
    """

    def __init__(self):
        self.src_url = 'https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/'
        self.file_list = ['TA.csv', 'PC.csv', 'SD.csv', 'SW.csv']
        self.env_file_dest = os.getenv('ASP_ENV_DATA_DIR', './data/asp_env')
        self.env_file_prepd = os.getenv('ASP_PREPD_DATA_DIR', './data/asp_prepd')

        # the input column from the original data (TA.csv, SW.csv etc) that contains
        # the date times for the various observations.
        self.date_col = 'DATE(UTC)'

        # the name of the column in the output data that will contain the date
        self.date_col_name = 'DATE'

        # calculate the current date and yesterday's date
        self.current_date = datetime.datetime.now()
        self.yesterday_date = self.current_date - datetime.timedelta(days=1)

        # the dateformat that will be used to format the date string in the output
        # file paths for the data.
        self.date_format = '%Y%m%d'

        # the name of the column that contains the climate station names in the ouput
        # data
        self.site_col_name = 'SITE'

        # the column name that will contain the cumulative precipitation data
        # ie the rain from yesterday at 7am to today at 7am
        self.precip_col_name = 'PC'

        # the column name for the snow water equivalent in mm at 7am today
        self.snow_col_name = 'SW'

        # the min and max temperature columns from yesterday at 7am to today at 7am
        self.temp_min_col_name = 'MINT'
        self.temp_max_col_name = 'MAXT'

        self.nan_value = 99999

        # overwriting the default start time in the start dates for today and yesterday
        self.default_start_time = self.yesterday_date.replace(hour=7,
                                                              minute=0,
                                                              second=0,
                                                              microsecond=0)
        self.default_end_time = self.current_date.replace(hour=7,
                                                          minute=0,
                                                          second=0,
                                                          microsecond=0)

        # the time window that will be used to calculate the min and max temperature
        self.temperature_start_time = self.default_start_time
        self.temperature_end_time = self.current_date.replace(hour=15,
                                                          minute=0,
                                                          second=0,
                                                          microsecond=0)


    def get_local_dir(self):
        """returns the local directory where the data will be stored, based on the
        date string

        :return: local directory
        :rtype: str
        """
        date_str = self.get_current_date_str()
        local_dir = os.path.join(self.env_file_dest,
                                 date_str)
        return local_dir

    def get_output_file(self):
        """calculates the output path for the ASP data based on the current date.

        :return: the file path where the output file will be stored
        :rtype: str
        """
        date_str = self.get_current_date_str()
        date_str_hiphen = self.get_current_date_str('%Y-%m-%d')
        output_file_name = f'ASP_daily-{date_str_hiphen}.csv'
        output_file = os.path.join(self.env_file_prepd,
                                   date_str,
                                   output_file_name)
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

class ProcessASPData:

    def __init__(self, config: Config):
        self.config = config

    def process(self):
        """processes the temperature / precipitation / snow water data then combines
        the dataframes into a single data frame by joining based on the site id, and
        finally dumps the data to a csv file.
        """
        output_file_name = self.config.get_output_file()
        output_dir_name = os.path.dirname(output_file_name)
        if not os.path.exists(output_dir_name):
            os.makedirs(output_dir_name)

        # debugging
        if os.path.exists(output_file_name):
            os.remove(output_file_name)

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
            temp_precip_df = pd.merge(temp_df,
                                    precip_df,
                                    how="outer",
                                    on=[self.config.site_col_name])
            temp_precip_snow_df = pd.merge(temp_precip_df,
                                        snoww_df,
                                        how="outer",
                                        on=[self.config.site_col_name])
            temp_precip_snow_df = temp_precip_snow_df.sort_values([self.config.site_col_name])



            # re-order the columns
            temp_precip_snow_df = temp_precip_snow_df[[self.config.site_col_name,
                    self.config.date_col_name,
                    self.config.temp_max_col_name,
                    self.config.temp_min_col_name,
                    self.config.precip_col_name,
                    self.config.snow_col_name]]
            # replace NaN with 99999 or the config.nodata_value

            temp_precip_snow_df[self.config.date_col_name] = self.config.default_end_time

            print(temp_precip_snow_df.head(28))
            temp_precip_snow_df.to_csv(output_file_name,
                                       encoding='utf-8',
                                       index=False,
                                       na_rep=self.config.nan_value)



    def extract_site_id(self, site_name):
        """extracts the site id from the site name, which is the first word in the
        site name

        :param site_name: site name
        :type site_name: string
        :return: site id
        :rtype: string
        """
        return site_name.split(' ')[0]

    def process_PC(self):
        local_dir = self.config.get_local_dir()
        local_file = os.path.join(local_dir, 'PC.csv')

        # read the csv into a dataframe
        df_pc = pd.read_csv(local_file,
                 parse_dates=[self.config.date_col],
                 encoding="ISO-8859-1")

        # rename the date column, mostly to take out the '(' and ')' characters that
        df_pc = df_pc.rename(
            columns={self.config.date_col: self.config.date_col_name})

        # filter for records that are for 7am yesterday and 7am today, based on default
        # times defined in config object
        df_pc_date_filter = df_pc.query(
            f'{self.config.date_col_name} == @self.config.default_start_time or ' +
            f'{self.config.date_col_name} ==  @self.config.default_end_time')

        # pivot the columns into rows for the various stations
        df_pc_format = df_pc_date_filter.melt(id_vars=[self.config.date_col_name],
                var_name=self.config.site_col_name,
                value_name='precipitation')

        # concat the values in the climate station column (default value 'site')
        # column to only include site id and remove the full name for the climate
        # station
        df_pc_format[self.config.site_col_name] = df_pc_format[
            self.config.site_col_name].apply(self.extract_site_id)

        # sort the values so we can get rid of the NaN values
        df_pc_format[self.config.precip_col_name] = df_pc_format.sort_values(
            [self.config.date_col_name, self.config.site_col_name]).groupby(
            self.config.site_col_name)['precipitation'].diff()
        df_precip_accum = df_pc_format.groupby([self.config.site_col_name]).agg(
            {self.config.precip_col_name: 'max'}).reset_index()
        print(df_precip_accum)
        return df_precip_accum

    def process_TA(self):
        """using the parameters defined in the config object will:
        * read the TA.csv file into a dataframe
        * restructure so that the individual station names become rows
        * filter out records for the current date as defined in the config object
        * calculate the min / max temperature for each station for the filtered
            records
        * restructure the station name to only include the station id

        :return: a pandas dataframe with the columns (SITE, DATE, MINT, MAXT)
        :rtype: pd.df
        """
        local_dir = self.config.get_local_dir()
        local_file = os.path.join(local_dir, 'TA.csv')
        LOGGER.debug(f"local file: {local_file}")

        # read the csv to a dataframe
        df = pd.read_csv(local_file,
                         parse_dates=[self.config.date_col],
                         encoding="ISO-8859-1")
        # rename the date column, mostly to take out the '(' and ')' characters that
        # make it tricky to work with
        df = df.rename(columns={self.config.date_col: self.config.date_col_name})

        # filter out records between yesterday based on config TA_start_time and
        #   TA_end_time properties
        df_date_filter = df.query(
            f'{self.config.date_col_name} > @self.config.temperature_start_time and {self.config.date_col_name} <= @self.config.temperature_end_time')

        # pivot the columns into rows for the different stations
        df_format = df_date_filter.melt(id_vars=[self.config.date_col_name],
                                        var_name=self.config.site_col_name,
                                        value_name='temperature')
        #
        df_format[self.config.site_col_name] = df_format[self.config.site_col_name].apply(self.extract_site_id)

        # summarize, getting the min and the max temperature
        df_min_max_t = df_format.groupby(
            self.config.site_col_name)['temperature'].agg(
            [(self.config.temp_min_col_name, 'min'),
             (self.config.temp_max_col_name, 'max')]).reset_index()
        df_min_max_t.insert(1, self.config.date_col_name, self.config.default_end_time)

        return df_min_max_t

    def process_SW(self):
        """get the snow water data... Looks like it just retrieves the value for 7am
        for the current date.
        """
        local_dir = self.config.get_local_dir()
        local_file = os.path.join(local_dir, 'SW.csv')
        LOGGER.debug(f"local file: {local_file}")

        # read the csv to a dataframe
        df = pd.read_csv(local_file,
                         parse_dates=[self.config.date_col],
                         encoding="ISO-8859-1")
        # rename the date column, mostly to take out the '(' and ')' characters that
        # make it tricky to work with
        df = df.rename(columns={self.config.date_col: self.config.date_col_name})

        # filter out records to only include for today at 7am
        df_date_filter = df.query(
            f'{self.config.date_col_name} == @self.config.default_end_time')

        print(df_date_filter)
        df_format = df_date_filter.melt(id_vars=[self.config.date_col_name],
                                        var_name=self.config.site_col_name,
                                        value_name=self.config.snow_col_name)
        df_format[self.config.site_col_name] = df_format[self.config.site_col_name].apply(self.extract_site_id)
        print(df_format.head(25))
        df_format = df_format.drop(self.config.date_col_name, axis=1)


        # drop the date column
        return df_format

class GetData:

    def __init__(self, config: Config):
        self.config = config

    def get_data(self):
        date_str = self.config.get_current_date_str()
        for remote_file in self.config.file_list:
            remote_url = os.path.join(self.config.src_url, remote_file)
            LOGGER.info(f'Downloading file: {remote_url}')
            local_dir = self.config.get_local_dir()
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            local_file = os.path.join(local_dir,
                                      remote_file)
            LOGGER.info(f"local dest {local_file}")

            if not os.path.exists(local_file):
                r = requests.get(remote_url, allow_redirects=True)
                if r.status_code == 200:
                    with open(local_file, 'wb') as fh:
                        fh.write(r.content)
                else:
                    LOGGER.error(f"error downloading file {remote_file} from {remote_url}, status code {r.status_code}" )

if __name__ == '__main__':

    # log config
    log_config_path = os.path.join(os.path.dirname(__file__), 'logging.config')
    logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
    LOGGER = logging.getLogger(__name__)
    LOGGER.info(f"starting {__name__}")

    # override config to debug
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.debug(f"logging level set to {LOGGER.level}")

    main = main()
    main.run()
