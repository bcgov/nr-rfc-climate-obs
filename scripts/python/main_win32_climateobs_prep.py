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
import sys

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

        # the anchor text for the export paths
        self.export_path_identifier = 'GROUPS'
        self.rows_to_keep_identifier = ['COFFEE', 'Ensemble V']

    def get_export_models(self, sheet):
        """returns a list of the locations that data is going to be exported to

        :param sheet: _description_
        :type sheet: _type_
        """
        values = self.get_values(sheet=sheet,
                    search_string=self.export_path_identifier,
                    offsets=[[1,1],[9,3]],
                    multiple=True)
        LOGGER.debug(f"values: {values}")

    def set_export_models(self, sheet, export_2_keep):
        """gets a reference to a ss and a list of keywords that represent the
        rows that should be kept, other rows will have their cells set to null

        so will search the spreadsheet for the text that identifies the start of the
        model definition section, then it will iterate over the model names.  If the
        model name is in the keep list the calls will be retained, if not, the row
        that defines the model will be set to null

        :param sheet: _description_
        :type sheet: _type_
        :param export_2_keep: _description_
        :type export_2_keep: _type_
        """
        # range contains the whole sheet
        sheet_range = self.get_sheet_max_range(sheet)
        col_row_list = self.get_cell_address(range=sheet_range,
                                             search_string=self.export_path_identifier)
        LOGGER.debug(f"col_row_list {col_row_list}")
        offset_cnt = 0
        row_list = list(range(1, 9))
        for col_offset in row_list:
            # always adding 1 to offset values to account for excel being base 1, but
            # lists in python being base 0
            LOGGER.debug(f"col_offset: {col_offset} {type(col_offset)}")
            col_offset = int(col_offset)
            cell_address_1 = col_row_list[0] + 1 + col_offset
            cell_address_2 = col_row_list[1] + 1 + 1
            model_name = sheet.Cells(cell_address_1, cell_address_2).Value
            LOGGER.debug(f"val: {model_name} {cell_address_1}, {cell_address_2}")
            if model_name not in export_2_keep:
                # delete values in this row.  range defines how many cols in the row
                # to zero out / null out
                for col_null_offset in range(0, 11):
                    col_ref_2_del = cell_address_2 + col_null_offset
                    model_name = sheet.Cells(cell_address_1, col_ref_2_del).Value
                    LOGGER.debug(f"DELETE: {model_name} {col_ref_2_del}")
                    sheet.Cells(cell_address_1, col_ref_2_del).Value = None

            #sheet.Cells(col_row_list[0] + 1 + offset[0], col_row_list[1] + 1 + offset[1]).Value = values[offset_cnt]
            #offset_cnt += 1

    def get_workbook(self, arg: str):
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
        # data\fwx\extracts\2023-09-26\2023-09-26.csv
        fwx_path = r'Z:\home\kjnether\rfc_proj\climate_obs\data\fwx\extracts\2023-09-26'
        self.get_FWX_paths(sheet=ops_sheet)
        self.set_FWX_paths(sheet=ops_sheet, new_path=fwx_path)

        # update the model data
        #self.get_export_models(sheet=ops_sheet)
        self.set_export_models(sheet=ops_sheet, export_2_keep=self.rows_to_keep_identifier)

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
        #ops_sheet = self.get_operations_ss()
        range = self.get_sheet_max_range(sheet)
        col_row_list = self.get_cell_address(range=range,
                                             search_string=search_string)
        offset_cnt = 0
        for offset in offsets:
            # always adding 1 to offset values to account for excel being base 1, but
            # lists in python being base 0
            cell_reference = sheet.Cells(col_row_list[0] + 1 + offset[0], col_row_list[1] + 1 + offset[1])
            cell_reference.Value = values[offset_cnt]

            # now update the hypertext link value
            cell_address = cell_reference.GetAddress(RowAbsolute=False, ColumnAbsolute=False)
            LOGGER.debug(f"cell address: {cell_address}")

            sheet.Hyperlinks.Add(Anchor=sheet.Range(cell_address),
                                 Address=values[offset_cnt])
            offset_cnt += 1

        # # adding 1 to each value because the first cell in excel is 1,1
        # ops_sheet.Cells(col_row_list[0] + 1 + 1,  col_row_list[1] + 1).Value = today_path
        # ops_sheet.Cells(col_row_list[0] + 1 + 2,  col_row_list[1] + 1).Value = yesterday_path

    def get_values(self, sheet, search_string, offsets, multiple=False):
        """used to extract values out of a spreadsheet.  Recieves a worksheet reference
        and a seach string.  The code will search for the search string
        location in the spreadsheet.  Having located the search string if multiple is
        set to false will search for the location of a cell relative to the search
         string.  if offsets of [1,0] are provided then it will return the value that
         is 1 row below the search string.  if offset of [0,1] are provided then will
         return the cell immediately to the right of the search string.  If you want
         multiple values returned then specify their offsets in a list... example for
         the two cells directly below the anchor point [[1,0], 2,0]]

         if multiple is 'True' then the offsets should take the following syntax:

         [[start row offset, start column offset], end row offset, end column offset]]


        :param sheet: a reference to an xl worksheet object
        :type sheet: worksheet
        :param search_string: the search string to find in the sheet
        :type search_string: str
        :param offsets: the offset locations to return based on the location of the
            anchor text.
        :type offsets: list[int]
        :param multiple: bool, defaults to False
        :type multiple: bool, optional
        :return: the values associated with the requested offsets / anchor text location
        :rtype: variable (whatever is in the cells)
        """
        range = self.get_sheet_max_range(sheet)
        col_row_list = self.get_cell_address(range=range,
                                             search_string=search_string)
        values = []
        LOGGER.debug(f'offsets: {offsets}')
        LOGGER.debug(f'col_row_list: {col_row_list}')
        if multiple == True:
            # if multiple the list must take the form:
            # [start row, start column], [end row, end_column]]
            # the returned data structure will take that form

            start_row_offset = offsets[0][0] + col_row_list[0]
            start_col_offset = offsets[0][1] + col_row_list[1]
            end_row_offset = offsets[1][0] + col_row_list[0]
            end_col_offset =  offsets[1][1] + col_row_list[1]


            row_values = range.Value[start_row_offset:end_row_offset]
            for rows in row_values:
                LOGGER.debug(f"rows: {rows}")
                subvals = rows[start_col_offset:end_col_offset]
                LOGGER.debug(f"subvals: {subvals}")
                values.append(subvals)
        else:
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
        """updates the automated snow pillow paths with the supplied path

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

        :param sheet: xl worksheet object to find the max range for
        :type: xl worksheet
        :return: a range object that contains the extent of the input sheet
        :rtype: xl range
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
        and returns that value

        :param sheet: an xl worksheet reference
        :type sheet: xl worksheet
        :return: returns the date value that is contained in the current date cell
        :rtype: str
        """
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
        """
        finds the 'OPERATIONS' sheet from the workbook and returns a reference to that
        object

        :return: reference to the xl worksheet that contains the OPERATIONS data. Its
                 the sheet with all the file paths in it.
        :rtype: xl worksheet
        """
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
    path_to_xl = r"C:\Kevin\ClimateDataOBS_2023.xlsm"

    climate_obs = ClimateObsXLUpdate(climate_obs_xl_path=path_to_xl)
    climate_obs.update_ss()

