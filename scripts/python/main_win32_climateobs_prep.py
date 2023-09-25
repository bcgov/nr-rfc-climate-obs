"""
* pulls the climate obs data down from the various locations
* opens up the xl spreadsheet
* finds the cells that need to be updated
* updates them with the new paths for the data
* attempts to run the various macros that do the actual imports

"""

import win32com.client
import logging.config
import os.path
import datetime

# setup logging
module_name = os.path.splitext(os.path.basename(__file__))[0]
cur_dir = os.path.dirname(__file__)
log_config_path = os.path.join(cur_dir, 'logging.config')
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
print(f"module name {module_name}")
LOGGER = logging.getLogger(module_name)
LOGGER.debug(f"starting {module_name}")

class ClimateObsXLUpdate:
    """
    methods to update various cells in the spreadsheet.
    """


    def __init__(self, climate_obs_xl_path:str):
        self.climate_obs_xl_path = climate_obs_xl_path
        if not os.path.exists(self.climate_obs_xl_path):
            msg = f"path to xl workbook: {self.climate_obs_xl_path} not found"
            raise FileNotFoundError(msg)

        # will get populated when the workbook is opened
        self.constants = None
        self.operation_sheet_name = 'OPERATION'
        self.xl_wb = self.get_workbook()

        # looking for cell with this value to find the current date
        self.current_date_identifier = 'CURRENT DATE:'
        self.current_date = datetime.datetime.now()
        self.current_date_format = '%Y-%m-%d'

        # this is the path where the XML MPOML data is located.  Should be two
        # cells below this entry, the first is for 'Today' and the second is
        # for 'Yesterday'
        self.MPOML_data_path_identifier = "XML DATA PATH"

        # this is the cell value that will be used to determine where to find the
        # ASP data
        self.ASP_data_path_identifier = "ASP DATA PATH"

        # the anchor text for the zxs data
        self.ZXS_data_path_identifier = 'ZXS-850 DATA PATH'

        # the anchor text for the wildfire data
        self.FWX_data_path_identifier = 'FIRE WEATHER DATA PATH'

    def get_workbook(self):
        LOGGER.info("opening xl workbook... may take a moment")
        xl = win32com.client.gencache.EnsureDispatch('Excel.Application')
        xl.Visible = True
        wb = xl.Workbooks.Open(self.climate_obs_xl_path)
        self.constants = win32com.client.constants
        return wb

    def get_MPOML_paths(self, sheet):
        """retrieves the path from the climate obs spreadsheet where the data ingestion
        macro is expecting the MPOML data to be.

        :param sheet: the worksheet object to search in
        :type sheet: worksheet
        :return: a list with two paths, the first is the path where the ingestion script
                 expects to find the data for 'today' and the second value is where
                 the data for 'yesterday' can be found
        :rtype: list
        """
        values = self.get_values(sheet=sheet,
                        search_string=self.MPOML_data_path_identifier,
                        offsets=[[1,0],[2,0]])
        LOGGER.debug(f"values for MPOML: {values}")
        return values

    def get_FWX_paths(self, sheet):
        values = self.get_values(sheet=sheet,
                        search_string=self.FWX_data_path_identifier,
                        offsets=[[1,0]])
        LOGGER.debug(f"values for MPOML: {values}")
        return values

    def set_FWX_paths(self, sheet, new_path):
        values = [new_path]
        offsets = [[1, 0]]
        self.set_values(sheet=sheet,
                        search_string=self.FWX_data_path_identifier,
                        offsets=offsets,
                        values=values)

    def set_MPOML_paths(self, sheet, today_path, yesterday_path):
        """Will replace existing values for the MPOML data, for today, and yesterday
        values.  These are the paths where the spreadsheet is expecting those data sets
        to exist.  Expects for today to find a data set that matches the pattern:
            - today_bc_20140121_e.xml
        and for yesterday the pattern:
            - yesterday_bc_20140121_e.xml

        Dates in those file paths will obviously be different

        :param sheet: a worksheet object, this is the sheet that will look for the MPOML
            paths and update them
        :type sheet: excel worksheet
        :param today_path: the path to where the 'today' data can be found
        :type today_path: str
        :param yesterday_path: the path to where the 'yesterday' data can be found
        :type yesterday_path: str
        """
        # range = self.get_sheet_max_range(sheet)
        # col_row_list = self.get_cell_address(range=range,
        #                                      search_string=self.MPOML_data_path_identifier)
        # # adding 1 to each value because the first cell in excel is 1,1
        # ops_sheet.Cells(col_row_list[0] + 1 + 1,  col_row_list[1] + 1).Value = today_path
        # ops_sheet.Cells(col_row_list[0] + 1 + 2,  col_row_list[1] + 1).Value = yesterday_path

        values = [today_path, yesterday_path]
        offsets = [[1, 0], [2,0]]
        self.set_values(sheet=sheet,
                        search_string=self.MPOML_data_path_identifier,
                        offsets=offsets,
                        values=values)

    def get_ZXS_paths(self, sheet):
        values = self.get_values(sheet=sheet,
                        search_string=self.ZXS_data_path_identifier,
                        offsets=[[1,0]])
        LOGGER.debug(f"values for ZXS: {values}")
        return values

    def set_ZXS_paths(self, sheet, new_path):
        values = [new_path]
        offsets = [[1, 0]]
        self.set_values(sheet=sheet,
                        search_string=self.ZXS_data_path_identifier,
                        offsets=offsets,
                        values=values)


    def update_ss(self):
        """
        pulls a copy of the ss, updates paths, and runs the import process
        """
        # ops_sheet is the 'OPERATIONS' worksheet object
        ops_sheet = self.get_operations_ss()
        LOGGER.debug(f"current sheet: {ops_sheet}")

        # getting the current date from the ss
        current_date = self.get_current_date(sheet=ops_sheet)
        LOGGER.debug(f"current_date: {current_date}")

        # get / set the path to the MPOML data
        paths = self.get_MPOML_paths(sheet=ops_sheet)
        LOGGER.debug(f"current today/yesterday paths: {paths}")
        today_path = r'Z:\home\kjnether\rfc_proj\climate_obs\data\mpoml\raw'
        yesterday_path = r'Z:\home\kjnether\rfc_proj\climate_obs\data\mpoml\raw'
        self.set_MPOML_paths(sheet=ops_sheet,
                             today_path=today_path,
                             yesterday_path=yesterday_path)

        # get / set the path to the Automated Snow Pillow  Data (ASP)
        path = self.get_ASP_paths(sheet=ops_sheet)
        LOGGER.debug(f"current path for asp data: {path}")
        # now update
        asp_path = r'Z:\home\kjnether\rfc_proj\climate_obs\data\asp_prepd\20230920'
        self.set_ASP_paths(sheet=ops_sheet, new_path=asp_path)

        # zxs data:
        zxs_path = r'Z:\home\kjnether\rfc_proj\climate_obs\data\zxs\raw\20230924'
        self.get_ZXS_paths(sheet=ops_sheet)
        self.set_ZXS_paths(sheet=ops_sheet, new_path=zxs_path)

        # wildfire data:
        fwx_path = 'Z:\home\kjnether\rfc_proj\climate_obs\data\fwx\raw'
        self.get_FWX_paths(sheet=ops_sheet)
        self.set_FWX_paths(sheet=ops_sheet, new_path=fwx_path)



    def set_values(self, sheet, search_string, offsets, values):
        """Used to update values in the spreadsheet.  Starts by searching the suppplied
        worksheet for the value defined in the parameter 'search_string'.  Having
        located the cell with that value, uses the offsets and values to update.

        The offset identifes where relative the found cell the values should be updated.

        example: searching for the cell with the value "ASP DATA" might be identifed
                 as row 4 column 10.  If the values I want to update are below that
                 value, and I want to update the next two cells I would specify and
                 offset of [[1,0], [2,0]] and values with:
                 ['new val cell 1', 'new val cell 2']

                 This would update the two cells directly underneath the cell with the
                 value "ASP DATA"

        :param sheet: worksheet object
        :type sheet: excel worksheet object
        :param search_string: the string that the anchor cell will be populated with
        :type seearch_string: str
        :param offsets: a list of lists where the inner list contains the row offset,
            followed by the column offset for where the subsequent values are located
        :type offsets: list
        :param values: a list of values to update the cells.  The number of values in
            this list should be the same as the number of values in the offset list
            will raise a valueError if this is not the case
        :type values: list(str)
        """
        ops_sheet = self.get_operations_ss()
        range = self.get_sheet_max_range(sheet)
        col_row_list = self.get_cell_address(range=range,
                                             search_string=search_string)
        offset_cnt = 0
        for offset in offsets:
            # always adding 1 to offset values to account for excel being base 1, but
            # lists in python being base 0
            ops_sheet.Cells(col_row_list[0] + 1 + offset[0], col_row_list[1] + 1 + offset[1]).Value = values[offset_cnt]
            offset_cnt += 1

        # # adding 1 to each value because the first cell in excel is 1,1
        # ops_sheet.Cells(col_row_list[0] + 1 + 1,  col_row_list[1] + 1).Value = today_path
        # ops_sheet.Cells(col_row_list[0] + 1 + 2,  col_row_list[1] + 1).Value = yesterday_path

    def get_values(self, sheet, search_string, offsets):
        range = self.get_sheet_max_range(sheet)
        col_row_list = self.get_cell_address(range=range,
                                             search_string=search_string)
        values = []
        for offset in offsets:
            value = range.Value[col_row_list[0] + offset[0]][col_row_list[1] + offset[1]]
            values.append(value)
        return values

    def get_ASP_paths(self, sheet):
        """
        extracts from the input spreadsheet the paths to where the ASP data is expected
        to be found

        :param sheet: the excel workbook sheet object to search for the ASP paths
        :type sheet: sheet
        :return: the paths to the asp data
        :rtype: str
        """
        values = self.get_values(sheet=sheet,
                                 search_string=self.ASP_data_path_identifier,
                                 offsets=[[1,0]])
        LOGGER.debug(f"values: {values}")
        return values

    def set_ASP_paths(self, sheet, new_path):
        """updates the automated snow pillow paths

        :param sheet: _description_
        :type sheet: _type_
        :param new_path: _description_
        :type new_path: _type_
        """
        self.set_values(sheet=sheet,
                        search_string=self.ASP_data_path_identifier,
                        offsets=[[1,0]],
                        values=[new_path])

    def get_sheet_max_range(self, sheet):
        """
        returns a range object that encapsulates all the data in the sheet
        """
        startCell = sheet.Cells(1, 1)
        startCellAddress = startCell.GetAddress(RowAbsolute=False, ColumnAbsolute=False)
        LOGGER.debug(f"start cell: {startCellAddress}")
        cell = sheet.Cells.SpecialCells(self.constants.xlCellTypeLastCell)
        cellAddress = cell.GetAddress(RowAbsolute=False, ColumnAbsolute=False)
        LOGGER.debug(f"cellAddress {cellAddress}")
        range = sheet.Range(f"{startCellAddress}:{cellAddress}")
        return range

    def get_current_date(self, sheet):
        """
        Goes into the sheet, finds value that aligns with CURRENT DATE:
        and returns that value:
        """
        # range = self.get_sheet_max_range(sheet)
        # col_row_list = self.get_cell_address(range=range,
        #                                      search_string=self.current_date_identifier)
        # LOGGER.debug(f"location of cell: {col_row_list}")
        # # assuming that the value is the next cell over to the right
        # cell_value = range.Value[col_row_list[0]][col_row_list[1] + 1]
        # LOGGER.debug(f"number of row: {len(range.Value)}")
        # LOGGER.debug(f"cell_value: {cell_value}, {type(cell_value)}")
        # return cell_value

        values = self.get_values(sheet=sheet,
                                 search_string=self.current_date_identifier,
                                 offsets=[[0,1]])
        LOGGER.debug(f"values for current date: {values}")
        return values[0]

    def get_cell_address(self, range, search_string):
        """searches the sheet for a given string and returns the cell that contains
        that string.

        :param sheet: input excel range object
        :type sheet: range
        :param search_string: the string in the sheet to search for
        :type search_string: str

        :return: a list containing the column / row positions, using base of 0, ie
                 the first element in the list is element 0.
        """
        rowcnt = 0
        breakrow = False
        location = []
        for row in range.Value:
            columncnt = 0
            for cell_value in row:
                #LOGGER.debug(f"cell {columncnt} {rowcnt} : {cell_value}")
                if ((cell_value) and isinstance(cell_value, str)) and search_string.upper() in cell_value.upper():
                    location = [rowcnt, columncnt]
                    breakrow = True
                    break
                columncnt += 1
            if breakrow:
                break
            rowcnt += 1
        return location

    def get_operations_ss(self):
        #sheet_names = [sheet.Name for sheet in wb.Sheets]
        self.xl_wb.Worksheets(self.operation_sheet_name).Activate()
        sheet = self.xl_wb.Worksheets(self.operation_sheet_name)
        return sheet



if __name__ == '__main__':
    # TODO: figure out injest of SS
    # need to figure out how the sync will take place for the climateobs model from
    # local on prem storage to object store
    # eventually replace this with code that goes out and aquires the ss.
    #
    path_to_xl = os.path.realpath(os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    '..',
                    'old_scripts',
                    'ClimateDataOBS_2023.xlsm'))

    path_to_xl = r'Z:\home\kjnether\rfc_proj\climate_obs\old_scripts\ClimateDataOBS_2023.xlsm'
    climate_obs = ClimateObsXLUpdate(climate_obs_xl_path=path_to_xl)
    climate_obs.update_ss()

