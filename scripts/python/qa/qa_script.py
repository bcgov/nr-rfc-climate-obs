"""
code that can be used to qa the differences between the raw data,
processed data and the data that was processed by the older R script
"""


import pandas as pd


class QA_data:

    def __init__(self, qa_config):
        self.qa_config = qa_config

class QA_Config:

    def __init__(self):
        # the date string that will be used to perform the qa of the data
        self.qa_date_str = '2023-09-05'
        self.climate_station_id = ''


