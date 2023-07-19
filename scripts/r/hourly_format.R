# Export hourly data
# clear all
rm(list = ls())

start.time <- Sys.time()

# load package
require(rio)
require(XML)
require(dplyr)
require(lubridate)
require(tibbletime)
require(magrittr)
require(tibble)


# path of input
#path <- paste0 ("V:/Real-time_Data/F_WX/SRC/")
#outputpath <- "V:/Real-time_Data/F_WX/HOURLY/"

start.date <- date(start.time)-1

path <- paste0 ("E:/Shared/Real-time_Data/F_WX/SRC/")
#path <- paste0 ("V:/Real-time_Data/F_WX/SRC/")

#STN_list<-rio::import(paste0(path,"Datamart swob-xml_station_list.xls"))

#Format file with data starting at 8 am PST: (8 hrs)
dt.start <- start.date+hours(8)
#Convert to UTC: (Built in time zones not used since they include daylight savings time)
dt.start.UTC <- dt.start+hours(8)


dt = dt.start
year<-format(dt,"%Y")
month<-format(dt,"%m")
day<-format(dt,"%d")

#List stations in directory:
#inputpath<-paste0("V:\\Real-time_Data\\F_WX\\HOURLY\\hpfx.collab.science.gc.ca\\",year,month,day,"\\")
inputpath<-paste0("E:\\Shared\\Real-time_Data\\F_WX\\HOURLY\\hpfx.collab.science.gc.ca\\",year,month,day,"\\")

#List of directories (one directory for each station):
dirlist1<-dir(path=inputpath)
#Sort directories by station numbers:
dirlist<-as.character(sort(as.integer(dirlist1)))
#Number of stations (directories):
dirlength = length(dirlist)

#Create blank dataframe with 24 columns to match expected format:
mat<-matrix(data = NA, nrow = 24*dirlength, ncol = 24)
output<-data.frame(mat)
colnames(output)<-c("station_code","weather_date","precipitation","temperature","relative_humidity","wind_speed","wind_direction","ffmc","isi","fwi","rn_1_pluvio1","snow_depth","snow_depth_quality","precip_pluvio1_status","precip_pluvio1_total","rn_1_pluvio2","precip_pluvio2_status","precip_pluvio2_total","rn_1_RIT","precip_RIT_Status","precip_RIT_total","precip_rgt","solar_radiation_LICOR","solar_radiation_CM3")

hh<-c("00","01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23")


for (j in 1:dirlength){ # Loop through all stations (j) #dirlength
  tryCatch({ #Added on 2022-04-29
    
  for (i in 1:24){ # Loop through 24 hour period
    dt = dt.start+hours(i-1) #24 hour period starting at 8am PST
    year<-format(dt,"%Y")
    month<-format(dt,"%m")
    day<-format(dt,"%d")
    
    ind = 24*(j-1)+i  #Each station/observation is its own row
    output[ind,1]<-dirlist[j] #First column is station number
    output[ind,2]<-paste0(year,month,day,hh[hour(dt)+1]) #Second column is date
    
    dt.utc = dt.start.UTC+hours(i-1) #Downloaded files are in UTC
    year.utc<-format(dt.utc,"%Y")
    month.utc<-format(dt.utc,"%m")
    day.utc<-format(dt.utc,"%d")
    current_date<-paste0(year.utc,"-",month.utc,"-",day.utc)
    inputpath<-paste0("E:\\Shared\\Real-time_Data\\F_WX\\HOURLY\\hpfx.collab.science.gc.ca\\",year.utc,month.utc,day.utc,"\\")
    #inputpath<-paste0("V:\\Real-time_Data\\F_WX\\HOURLY\\hpfx.collab.science.gc.ca\\",year.utc,month.utc,day.utc,"\\")
    
    # read TA
      #Check if directory and filename exist:
    if(dir.exists(paste0(inputpath,dirlist[j]))==TRUE){
        if(file.exists(paste0(inputpath,dirlist[j],"\\",current_date,"-",hh[hour(dt.utc)+1],"00-bc-wmb-",dirlist[j],"-AUTO-swob.XML"))==TRUE){
          #Parse XML file:
          data_single <- xmlParse(paste0(inputpath,dirlist[j],"\\",current_date,"-",hh[hour(dt.utc)+1],"00-bc-wmb-",dirlist[j],"-AUTO-swob.XML"))
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
    # print(rootnode[[1]][[1]][[7]][[1]])
    }
  }
    
  }, error = function(err) { #2022-04-29
    # error handler picks up where error was generated
    print(paste("Skip the station ID",dirlist[j],"because of data error:",err))
    
  })
  
}
  


end.time <- Sys.time()
time.taken <- end.time - start.time
time.taken

#2022-04-30##########################
# Remove station 387;  I am not sure whether the null records will impact the data import, so it is removed for now.
output<-output[rowSums(is.na(output)) != ncol(output), ] #remove all NA row cases
# Remove station 387 case; Need to revised this approach later
output<-dplyr::filter(output,station_code!="387")
###########################################################

year<-format(end.time,"%Y")
month<-format(end.time,"%m")
day<-format(end.time,"%d")

fpath <- paste0("E:/Shared/Real-time_Data/F_WX/HOURLY/",year,"-",month,"-",day)
#fpath <- paste0("V:/Real-time_Data/F_WX/output/",year,"-",month,"-",day)

outputpath <- paste0("E:/Shared/Real-time_Data/F_WX/HOURLY/",year,"-",month,"-",day,"/")
#outputpath <- paste0("V:/Real-time_Data/F_WX/output/",year,"-",month,"-",day,"/")
#outputpath <- "E:/Shared/Real-time_Data/F_WX/HOURLY/"

if (!file.exists(fpath)){
  dir.create(fpath)
}

output2 <- output
output2[,1] <- paste0('"',output[,1],'"')
output2[,2] <- paste0('"',output[,2],'"')

rio::export(output,paste0(outputpath,current_date,".csv"))
#rio::export(output,paste0("E:/Shared/Real-time_Data/F_WX/output/","HourlyWeatherAllFields_WA.txt"))
write.table(output2, paste0("E:/Shared/Real-time_Data/F_WX/output/","HourlyWeatherAllFields_WA.txt"), append = FALSE, sep = ",", dec = ".",row.names = FALSE, col.names = TRUE, quote = FALSE)
#write.table(output2, paste0("V:/Real-time_Data/F_WX/output/","HourlyWeatherAllFields_WA.txt"), append = FALSE, sep = ",", dec = ".",row.names = FALSE, col.names = TRUE, quote = FALSE)
