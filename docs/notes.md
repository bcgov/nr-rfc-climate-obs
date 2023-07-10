# Overview

This doc contains notes that are gathered during the discovery phase where I 
am trying to document existing processes.  It is rough notes that are used to 
construct other documentation.

The following are the root datasets that are consumed by the clever/coffee model data
injestion routines:

* \\DRAIN.dmz\Shared\MPOML\Today
* \\DRAIN.dmz\Shared\MPOML\Yesterday
* \\DRAIN.dmz\Shared\Real-time_Data\ASP_daily
* \\DRAIN.dmz\Shared\Real-time_Data\F_WX\output
* \\DRAIN.dmz\Shared\ZXS


# MPOML - Today

A GML (XML) file with a bunch of point data for surface weather.

### Schedule - Daily 8:15am

The script xml_daily.bat pulls the following resource from the federal government 
data store.

``` cmd
SET OUT_FOLDER=E:\Shared\MPOML\Today
SET OUT_FOLDERy=E:\Shared\MPOML\Yesterday

SET URL_today=https://dd.weather.gc.ca/observations/xml/BC/today/
SET URL_yesterday=https://dd.weather.gc.ca/observations/xml/BC/yesterday/

# Equivalent URL from HPFX:
# https://hpfx.collab.science.gc.ca/20230627/observations/xml/BC/today/
# https://hpfx.collab.science.gc.ca/20230627/observations/xml/BC/yesterday/

%SC_FOLDER%\Wget.exe --no-check-certificate %URL_today%today_bc_%YYYY%%MT%%DD%_e.xml
%SC_FOLDER%\Wget.exe --no-check-certificate %URL_yesterday%yesterday_bc_%YYYY%%MT%%DD%_e.xml
```

Above are the key components to the windows script that pulls the data down.

then there is this script for hourly data

```
SET OUT_FOLDER=E:\Shared\MPOML\HOURLY
SET URL_HOURLY=http://hpfx.collab.science.gc.ca/%YYYY%%MT%%DD%/WXO-DD/observations/xml/BC/hourly/
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%00_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%01_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%02_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%03_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%04_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%05_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%06_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%07_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%08_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%09_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%10_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%11_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%12_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%13_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%14_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%15_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%16_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%17_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%18_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%19_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%20_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%21_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%22_e.xml
  %SC_FOLDER%\Wget.exe %URL_HOURLY%hourly_bc_%YYYY%%MT%%DD%23_e.xml

```

After data is downloaded runs ASP_daily_climate.bat which runs 
an R script

Think asp daily might come from the DCS toolkit stuff.


# ASP_daily 

### Schedule - Daily 8:40am

Schedule calls:
`E:\Shared\Real-time_Data\ASP_daily_R\SRC\ASP_daily_climate.bat`

The bat file calls:
`E:\Shared\Real-time_Data\ASP_daily_R\SRC\ASP_daily_climate.R`

inputs:
`E:/Shared/ASP_Data/TA.csv`
`E:/Shared/ASP_Data/PC.csv`
`E:/Shared/ASP_Data/SW.csv`

** These scripts come from params_wy_download.bat

outputs:

* note: these two files are the same files, but are output to 
        these two different locations

`E:\Shared\Real-time_Data\ASP_daily_R\ASP_daily-<YYYY-MM-DD>.csv`
`E:\Shared\Real-time_Data\ASP_daily\ASP_daily-<YYYY-MM-DD>.csv`

and... 
`E:\Shared\Real-time_Data\ASP_daily_R\ASP_daily-<YYYY-MM-DD>_yesterday.csv`


# params_wy_download.bat

inputs:
https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/PC.csv
https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/SD.csv
https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/SW.csv
https://www.env.gov.bc.ca/wsd/data_searches/snow/asws/data/TA.csv

### Schedule 

\\DRAIN.dmz\Shared\Real-time_Data\ASP_daily

**note:** looks like this script pulls data to the folder E:\Shared\ASP_Data\Downloaded however the ASP_Daily pulls from E:\Shared\ASP_Data, no idea how that data gets there!
