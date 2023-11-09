"""
Will pull the data for the fire weather stations from the wildfire data mart api
"""


import datetime
import json
import logging.config
import os.path
import pprint
from typing import Union

import fwx_typedicts
import requests

# setting up the logging
cur_path = os.path.dirname(__file__)
logger_name = os.path.basename(__file__).split('.')[0]
print(logger_name)
log_config_path = os.path.join(cur_path, 'logging.config')
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
LOGGER = logging.getLogger(logger_name)
LOGGER.info(f"starting {logger_name}")
LOGGER.debug(f"cur_path: {cur_path}")

class WildfireAPI:

    def __init__(self, url='https://bcwsapi.nrs.gov.bc.ca/wfwx-datamart-api/v1',
                 end_date:datetime=None,
                 start_date:datetime=None):
        """the constructor method for the class, setup to recieve some parameters that
        define what data should be retrieved

        :param url: _description_, defaults to 'https://bcwsapi.nrs.gov.bc.ca/wfwx-datamart-api/v1'
        :type url: str, optional
        :param date_toquery: a datetime object that defines the data that should be
            retrieved from the api, defaults to None
        :type date_toquery: datetime, optional
        """
        self.api_url = url
        self.standard_date_time_end = end_date
        self.standard_date_time_start = start_date
        if not self.standard_date_time_end:
            self.standard_date_time_end = datetime.datetime.now()
            self.standard_date_time_end = self.standard_date_time_end.replace(
                hour=8,
                minute=0,
                second=0,
                microsecond=0)

        if not self.standard_date_time_start:
            self.standard_date_time_start = (self.standard_date_time_end -
                                             datetime.timedelta(days=1))
            self.standard_date_time_start = self.standard_date_time_start.replace(
                hour=9,
                minute=0,
                second=0,
                microsecond=0)


        self.date_time_query_fmt = '%Y%m%d%H'

        # the api looks like it reports the weather data up to the time in the timestamp
        # however the csv reports the same record with a time stamp that contains
        # the start time up to the next hour.

        # this is an adjustment factor so the data from the api and the csv can be
        # compared.
        self.station_time_adjustment = -1

        # defines the data that should be exported to the csv, and also creates a
        # mapping of the column names from the api, and then what those columns should
        # be called when they are dumped.  Not sure where some of the values are comming
        # from as there are no values from the api that line up with the data in the
        # ftp site.  When this happens a 3 column list is provided where the first value
        # is '' the second is the output column and the third is the default value for
        # this padded column.
        self.hourly_properties_to_export = [
            ['stationCode', 'station_code'],
            ['weatherTimestamp', 'weather_date'],
            ['precipitation','precipitation'],
            ['temperature', 'temperature'],
            ['relativeHumidity', 'HOURLY_RELATIVE_HUMIDITY'],
            ['windSpeed', 'HOURLY_WIND_SPEED'],
            ['windDirection', 'HOURLY_WIND_DIRECTION'],
            ['windGust', 'HOURLY_WIND_GUST'],
            ['fineFuelMoistureCode', 'HOURLY_FINE_FUEL_MOISTURE_CODE'],
            ['initialSpreadIndex', 'HOURLY_INITIAL_SPREAD_INDEX'],
            ['fireWeatherIndex', 'HOURLY_FIRE_WEATHER_INDEX'],
            ['', 'PRECIPITATION', ''],
            ['', 'FINE_FUEL_MOISTURE_CODE', ''],
            ['', 'INITIAL_SPREAD_INDEX', ''],
            ['', 'FIRE_WEATHER_INDEX', ''],
            ['', 'DUFF_MOISTURE_CODE', ''],
            ['', 'DROUGHT_CODE', ''],
            ['', 'BUILDUP_INDEX', ''],
            ['', 'DANGER_RATING', ''],
            ['', 'RN_1_PLUVIO1', 0],
            ['', 'SNOW_DEPTH', 0],
            ['', 'SNOW_DEPTH_QUALITY', ''],
            ['', 'PRECIP_PLUVIO1_STATUS', 0],
            ['', 'PRECIP_PLUVIO1_TOTAL', 0]
        ]


    def get_all_stations_hourlies(self, out_file: Union[None, str]=None):
        """This is the main entry point for the class.  It will get all the stations,
        then iterate over each station and retrieve the data associated with that
        station.  The data for each station gets cached in memory.  Once all the data
        has been retrieved it gets written to a file.  The name of the file comes from
        the `out_file` parameter.

        If no out_file parameter is provided it will look to the environment variable
        F_WX_DATA_DIR.  If that parameter is not set it will default to ./data/fwx

        :param out_file: If you want to override the default location of the outfile it
            can be provided here
        :type out_file: str, optional
        """

        station_codes = self.get_station_codes()

        LOGGER.debug(f"station_codes: {station_codes}")
        station_hourlies = []
        cnt = 0

        if not out_file:
            out_file = self.get_file_path()

        if not os.path.exists(out_file):
            for station_code in station_codes:
                LOGGER.debug(f"working on station: {station_code}")
                station_hourly = self.get_hourlies(station_code)
                #self.pprint(station_hourly, output_json=False)

                station_hourlies.extend(station_hourly)
                cnt += 1
            if out_file:
                with open(out_file, 'w') as f:
                    header_values = ','.join(
                        [property[1] for property in self.hourly_properties_to_export])
                    f.write(header_values + '\n')
                    for station_hourly in station_hourlies:
                        row_str = self.get_hourly_row(station_hourly)
                        f.write(row_str)
        else:
            LOGGER.info(f"Doing nothing, the output file: {out_file} already exists")

    def get_hourly_row(self, station_hourly: dict) -> str:
        """gets the hourly row for a given station

        :param station_hourly: dictionary with the station hourly data
        :type station_hourly: dict
        :return: extracts the values from the station_hourly dict and returns a comma
            delimited string
        """
        hourly_row = []
        weatherTimeStamp_datetime = datetime.datetime.strptime(
            station_hourly['weatherTimestamp'],
            '%Y%m%d%H')
        weatherTimeStamp_datetime_corrected = weatherTimeStamp_datetime - \
             datetime.timedelta(hours=1)
        station_hourly['weatherTimestamp'] = \
            weatherTimeStamp_datetime_corrected.strftime('%Y%m%d%H')
        LOGGER.debug(f"station_hourly timestamp: {station_hourly['weatherTimestamp']}")

        for property in self.hourly_properties_to_export:

            if property[0]:
                hourly_row.append(station_hourly[property[0]])
            else:
                hourly_row.append(property[2])
        hourly_row_str_vals = [str(val) for val in hourly_row]
        hourly_row_str = ','.join(hourly_row_str_vals) + '\n'
        return hourly_row_str

    def get_station_codes(self) -> list[str]:
        """queries all the stations and returns a list of only the station codes sorted
        in numeric order

        :return: list of station codes returned by the api
        :rtype: list(str)
        """
        stations = self.get_stations()
        # convert to int so we can do a numeric sort
        station_codes = [int(station['stationCode']) for station in stations]
        station_codes.sort()
        # cast back to str
        LOGGER.debug(f"station_codes = {station_codes}")
        station_codes = [str(station) for station in station_codes]

        LOGGER.debug(f"total number of stations {len(station_codes)}")
        LOGGER.debug(f"station codes: {station_codes} {len(station_codes)}")
        return station_codes

    def get_stations(self) -> list[fwx_typedicts.Station]:
        """hits the api and get a list of stations, reformats the json into a dict
        where the key is the station code

        :return: _description_
        :rtype: _type_
        """
        url = f'{self.api_url}/stations'
        stations = self.get_all_pages(url)
        LOGGER.debug(f"number of stations: {len(stations)}")
        return stations

    def get_station(self, station_code:str) -> fwx_typedicts.WeatherStation:
        """retrieves the data associated with a specific weather station

        :param station_code: the station code who's data should be retrieved
        :type station_code: str
        :return: dictionary with the data for the station
        :rtype: dict
        """
        url = f'{self.api_url}/stations/{station_code}'
        r = requests.get(url)
        r_data = r.json()
        return r_data

    def get_all_pages(self, url: str, params={}) -> list[dict]:
        """gets all pages for a given url and query, for each page extracts the values
        in the 'collection' property, and adds all the elements to a list that is
        ultimately returned

        :param url: an api url to hit that potentially has multiple pages
        :type url: str
        :param query: any parameters that should be added to the url request
        :type query: _type_
        :return: a list of all the elements in the 'collection' property for the url
            end point
        :rtype: list
        """
        params['pageNumber'] = 1
        r = requests.get(url, params=params)
        r_data = r.json()
        station_codes = [station['stationCode'] for station in r_data['collection']]
        LOGGER.debug(f"station codes: {station_codes}")

        all_pages = r_data['collection']

        if r_data['totalPageCount'] > 1:
            for page_cnt in range(2, r_data['totalPageCount'] + 1):
                params['pageNumber'] = page_cnt
                r = requests.get(url, params=params)
                r_data = r.json()
                all_pages.extend(r_data['collection'])
        return all_pages

    def get_hourlies(self, station_code: str) -> list[fwx_typedicts.WeatherStation]:
        """
        needs to get the last 24 hours of data for all stations

        gets the timestamps for:
        2023092612
        2023092706


        :param station_code: the input station code
        :type station_code: str
        :return: the hourly data for a specific station for the time range that is
            defined in the properties:
                * standard_date_time_start
                * standard_date_time_end
        :rtype: list(dict)
        """

        url = f'{self.api_url}/hourlies'
        start_time_str = self.standard_date_time_start.strftime(
            self.date_time_query_fmt)
        end_time_str = self.standard_date_time_end.strftime(self.date_time_query_fmt)
        query = {'stationCode': station_code,
                 'pageNumber': 1,
                 'from': f'{start_time_str}',
                 'to': f'{end_time_str}'}

        # get the first page
        r = requests.get(url, params=query)
        r_data = r.json()
        all_pages = r_data['collection']

        # get the rest of the pages if there are any
        if r_data['totalPageCount'] > 1:

            for page_cnt in range(r_data['totalPageCount']):
                query['pageNumber'] = page_cnt
                r = requests.get(url, params=query)
                r_data = r.json()
                all_pages.extend(r_data['collection'])
        return all_pages

    def pprint(self, data_dict: dict, output_json=False):
        """gets data_dict struct, usually a python dict that originated from json and
        pretty prints it

        Used for debugging / viewing the results of various api queries

        :param data_dict: the input data struct to be pretty printed
        :type data_dict: dict
        :param output_json: if true will print json string instead of python data struct
            as string
        :type output_json: bool, optional
        """
        if json:
            data_dict_json = json.dumps(data_dict, indent=4, sort_keys=True)
            print(data_dict_json)
        else:
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(data_dict)

    def get_file_path(self) -> str:
        """
        returns the path to where the file should be saved based on ...

        the output path is built from the env var: F_WX_DATA_DIR
        example: F_WX_DATA_DIR/YYYY-MM-DD/YYYY-MM-DD.csv

        :return: the path to where the file should be saved
        :rtype: str
        """
        fwx_root = os.getenv('F_WX_DATA_DIR', './data/fwx/extracts')
        file_date_str = self.standard_date_time_end.strftime('%Y-%m-%d')
        fwx_out_dir = os.path.join(fwx_root, file_date_str)
        if not os.path.exists(fwx_out_dir):
            os.makedirs(fwx_out_dir)

        fwx_out_dir = os.path.join(fwx_out_dir, f"{file_date_str}.csv")
        LOGGER.debug(f"out_file {fwx_out_dir}")
        return fwx_out_dir



if __name__ == '__main__':
    wf_api = WildfireAPI()
    hourlies = wf_api.get_all_stations_hourlies()
