# Export hourly data
# clear all

# commenting out, until understand what its doing, probably a more precise way of
# cleaning up files
#rm(list = ls())


# load package
require(rio)
require(XML)
require(dplyr)
require(lubridate)
require(tibbletime)
require(magrittr)
require(tibble)
require(fs)
require(logger)

logger <- layout_glue_generator(
    format <-
    "{pid}/{namespace}/{fn} {time} {level}: {msg}")

log_layout(logger)
logger::log_threshold(DEBUG)

start.time <- Sys.time()

input_date_str <- format(start.time,"%Y%m%d")

DATA_DIR = Sys.getenv("F_WX_DATA_DIR")
RAW_DATA_DIR <- fs::path(DATA_DIR, "raw", "/", input_date_str)
OUTPUT_DATA_DIR <- fs::path(DATA_DIR, "extracts", "/")
logger::log_debug("DATA_DIR: {DATA_DIR}")
logger::log_debug("OUTPUT_DATA_DIR: {OUTPUT_DATA_DIR}")

output_date_str <- format(start.time,"%Y-%m-%d")
outputpath <- fs::path(OUTPUT_DATA_DIR, output_date_str)
output_file <- fs::path(outputpath, paste0(output_date_str,".csv"))

output_hourly_weather = fs::path(OUTPUT_DATA_DIR, "HourlyWeatherAllFields_WA.txt")

if (!file.exists(OUTPUT_DATA_DIR)){
  dir.create(OUTPUT_DATA_DIR)
}

#Format file with data starting at 8 am PST: (8 hrs)
logger::log_debug("start.time is: {start.time}")

# WHY -1??? - subracts a day from today, so getting yesterdays observations?
start.date <- date(start.time)-1
logger::log_debug("start date is: {start.date}  start.time: {start.time}")
# why add 8 hours? - makes the dt.start 8am
dt.start <- start.date+hours(8)
logger::log_debug("start date:  {start.date} dt:  {dt.start}")
#Convert to UTC: (Built in time zones not used since they include daylight savings time)
dt.start.UTC <- dt.start+hours(8)

logger::log_debug("start date UTC: {dt.start.UTC}")
input_date_str <- format(dt.start,"%Y%m%d")
logger::log_debug("input_date_str: {input_date_str}")

#List stations in directory:
inputpath <- fs::path(RAW_DATA_DIR, input_date_str)
logger::log_debug("inputpath: {inputpath}")


#List of directories (one directory for each station):
dirlist1<-dir(path=inputpath)
#Sort directories by station numbers:
dirlist<-as.character(sort(as.integer(dirlist1)))
#Number of stations (directories):
dirlength <- length(dirlist)

#Create blank dataframe with 24 columns to match expected format:
mat<-matrix(data = NA, nrow = 24*dirlength, ncol = 24)
output<-data.frame(mat)
colnames(output)<-c("station_code", "weather_date", "precipitation", "temperature",
                    "relative_humidity", "wind_speed", "wind_direction" ,"ffmc",
                    "isi", "fwi", "rn_1_pluvio1", "snow_depth", "snow_depth_quality",
                    "precip_pluvio1_status", "precip_pluvio1_total", "rn_1_pluvio2",
                    "precip_pluvio2_status", "precip_pluvio2_total", "rn_1_RIT",
                    "precip_RIT_Status", "precip_RIT_total", "precip_rgt",
                    "solar_radiation_LICOR", "solar_radiation_CM3")

hh<-c("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
      "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23")


for (j in 1:dirlength){ # Loop through all stations (j) #dirlength
  tryCatch({ #Added on 2022-04-29

  for (i in 0:23){ # Loop through 24 hour period, should probably just use a counter
    dt <- dt.start+hours(i) #24 hour period starting at 8am PST
    station_date_str <- format(dt,"%Y%m%d")

    ind <- 24*(j-1)+i  #Each station/observation is its own row
    output[ind,1] <- dirlist[j] #First column is station number
    output[ind,2] <- paste0(station_date_str, hh[hour(dt)+1]) #Second column is date

    dt.utc <- dt.start.UTC+hours(i) #Downloaded files are in UTC
    station_date_UTC_str1 <- format(dt.utc, "%Y-%m-%d")
    station_date_UTC_str2 <- format(dt.utc, "%Y%m%d")

    inputpath<-fs::path(RAW_DATA_DIR, station_date_UTC_str2)
    logger::log_debug("inputpath: {inputpath}")

    logger::log_debug("dirlist[j]: {dirlist[j]}")
    dir_path <- fs::path(inputpath, dirlist[j])
    logger::log_debug("dir_path: {dir_path}")
    #paste0(inputpath,dirlist[j],"\\",current_date,"-",hh[hour(dt.utc)+1],"00-bc-wmb-",dirlist[j],"-AUTO-swob.XML")

    # calculate the output file name and path
    file_name <- paste0(station_date_UTC_str1,"-",hh[hour(dt.utc)+1],"00-bc-wmb-",dirlist[j],"-AUTO-swob.xml")
    logger::log_debug("file_name: {file_name}")
    file_path <- fs::path(dir_path, file_name)
    logger::log_debug("file_path: {file_path}")

    # read TA
    #Check if directory and filename exist:
    if (dir.exists(dir_path) == TRUE){
        if (file.exists(file_path) == TRUE) {
          logger::log_debug("file exists: {file_path}")
          #Parse XML file:
          data_single <- xmlParse(file_path)
          rootnode <- xmlRoot(data_single)
          rm(data_single)

          #Acess node of XML file which contains the observation data:
          xml_data <- rootnode[[1]][[1]][[7]][[1]]
          rootsize <- xmlSize(xml_data)
          xmlList <- xmlToList(xml_data)

          for (k in 1:rootsize) { #Loop through each observation in XML file:
            if (xmlList[[k]][["qualifier"]][["value"]]=="100") {
              xml_name <-xmlList[[k]][[".attrs"]][["name"]]
              xml_value <-xmlList[[k]][[".attrs"]][["value"]]

              if (xml_name=="rnfl_amt_pst1hr") { #If observation is needed, save to output:
                output[ind,3]<-as.numeric(xml_value)
              } else if (xml_name=="air_temp") {
                output[ind,4]<-as.numeric(xml_value)
              } else if (xml_name=="rel_hum") {
                output[ind,5]<-as.numeric(xml_value)
              } else if (xml_name=="avg_wnd_spd_10m_pst10mts") {
                output[ind,6]<-as.numeric(xml_value)
              } else if (xml_name=="avg_wnd_dir_10m_pst10mts") {
                output[ind,7]<-as.numeric(xml_value)
              }
            }
          }
        }
    }
  }

  }, error = function(err) { #2022-04-29
    # error handler picks up where error was generated
    logger::log_debug(paste("Skip the station ID",dirlist[j],"because of data error:",err))

  })

}


# calculate this at the start of the code
end.time <- Sys.time()
time.taken <- end.time - start.time
time.taken
logger::log_debug("start_time is: {start.time} end time is: {end.time} ")

#2022-04-30##########################
# Remove station 387;  I am not sure whether the null records will impact the data import, so it is removed for now.
output<-output[rowSums(is.na(output)) != ncol(output), ] #remove all NA row cases
# Remove station 387 case; Need to revised this approach later
output<-dplyr::filter(output,station_code!="387")
###########################################################

logger::log_debug(paste0("input_date_str", input_date_str))
logger::log_debug(paste0("output_date_str", output_date_str))

logger::log_debug("outputpath directory is: {outputpath}")


# if fails need to make sure there is a trailing '\' character on this string
if (!file.exists(outputpath)){
  # if fails need to make sure there is a trailing '\' character on this string
  dir.create(outputpath)
}

output2 <- output
output2[,1] <- paste0('"',output[,1],'"')
output2[,2] <- paste0('"',output[,2],'"')
#logger::log_debug("output2: {output2}")

rio::export(output,output_file)
write.table(output2, output_hourly_weather, append = FALSE, sep = ",", dec = ".",row.names = FALSE, col.names = TRUE, quote = FALSE)
