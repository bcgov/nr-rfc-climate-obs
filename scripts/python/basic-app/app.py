from shiny import App, render, ui, reactive
import matplotlib.pyplot as plt
import numpy as np
import climate_utils
import os
import datetime

objpath = 'ClimateOBS'
year = '2024'
ClimateOBShourly_raw_path = os.path.join(objpath,f'ClimateOBS_hourly_raw_{year}.parquet')
ClimateOBS_hrly_raw = climate_utils.objstore_to_df(ClimateOBShourly_raw_path)
TA_hrly_raw = ClimateOBS_hrly_raw.loc["TA"].copy()
PC_hrly_raw = ClimateOBS_hrly_raw.loc["PC"].copy()
station_list = list(TA_hrly_raw.columns)

current_date = datetime.datetime.now() - datetime.timedelta(days=1)
start_dt = current_date - datetime.timedelta(days=1)
start_date = start_dt.strftime('%Y-%m-%d')
end_date = current_date.strftime('%Y-%m-%d')

app_ui = ui.page_fluid(
    ui.output_text_verbatim("txt", placeholder=True),
    ui.layout_columns(
        ui.input_date_range("daterange", "Date range", start=start_date,end=end_date),
         ui.input_select("stn_select","Select an Option Below:", choices = station_list),
    ),
    ui.input_action_button("get_data", "Get Data"),
    ui.output_plot("p", brush={"direction":"x"}),
)


def server(input, output, session):
    @render.text
    def txt():
        #return f"start: {input.daterange()[0]} end: {input.daterange()[1]}"
        #return f"start: {input.plot_brush()[0]} end: {input.plot_brush()[1]}"
        if input.p_brush() is not None:
            #x_coordinates = input.p_brush()['xmin']
            xmin=input.p_brush()['xmin']
            xmax=input.p_brush()['xmax']
            dt_min = datetime.datetime.fromordinal(int(xmin)+719163) + datetime.timedelta(days=(xmin % 1))
            dt_max = datetime.datetime.fromordinal(int(xmax)+719163) + datetime.timedelta(days=(xmax % 1))
            return f"Selected X Coordinates: {dt_min}, {dt_max}"
        else:
            return "No brush selection"

    @render.plot
    def p():
        #fig, ax = plt.subplots()
        #ax.plot([0,1,2,3],[0,1,2,3])
        fig, ax = plt.subplots()
        ax.plot(subset_data())
        return fig

    @reactive.event(input.get_data)
    def subset_data():
        start = input.daterange()[0]
        end = input.daterange()[1]
        stn = input.stn_select()

        return TA_hrly_raw.loc[start:end,stn]


app = App(app_ui, server)
