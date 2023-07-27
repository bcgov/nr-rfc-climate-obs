# clear all
rm(list = ls())
# Have to deal with logic variable

# load package
require(rio)
require(dplyr)
require(lubridate)
require(tibbletime)
require(magrittr)
require(tibble)

# path of input
path <- paste0("E:/Shared/ASP_Data/")
outputpath <- "E:/Shared/Real-time_Data/ASP_daily_R/"

#path <- paste0 ("V:/ASP_Data/") # Use Data BC's data
#outputpath <- "V:/Real-time_Data/ASP_daily_R/"

#Get current PDT date
current_date<-Sys.Date()#
current_date<-as.character(current_date)
yesterday<-Sys.Date()-1   ##
yesterday<-as.character(yesterday)

Time <- factor("07:00:00") # 
hour = format(as.POSIXct(Time,format="%H:%M:%S"),"%H")
minute = format(as.POSIXct(Time,format="%H:%M:%S"),"%M")
second = format(as.POSIXct(Time,format="%H:%M:%S"),"%S")

Time2 <- factor("15:00:00") #
hour2 = format(as.POSIXct(Time2,format="%H:%M:%S"),"%H")
minute2 = format(as.POSIXct(Time2,format="%H:%M:%S"),"%M")
second2 = format(as.POSIXct(Time2,format="%H:%M:%S"),"%S")

hms <-paste(hour,minute,sep=":")  #Delete second
hms2 <-paste(hour2,minute2,sep=":")

PC_starttime<-paste(yesterday,hms,sep=" ") # yesterday
PC_endtime<-paste(current_date,hms,sep=" ") # today
Tmin_endtime<-paste(current_date,hms2,sep=" ") # today

input_TA <- paste0(path,"TA.csv")
TA<-import(input_TA)
colnames(TA)[1] <- "datetime"
NC<-NCOL(TA)



#SW
input_SW <- paste0(path,"SW.csv")
SW<-import(input_SW)
colnames(SW)[1] <- "datetime"

# 
SW<-SW %>%
  filter(.,datetime==PC_endtime) #%>%


#PC
input_PC <- paste0(path,"PC.csv")
PC<-rio::import(input_PC)
colnames(PC)[1] <- "datetime"

# 
PC<-PC %>%
  dplyr::filter(.,datetime>=PC_starttime) #%>%

PC_today<-dplyr::filter(PC,datetime==PC_endtime)
PC_yesterday<-dplyr::filter(PC,datetime==PC_starttime)

rain<-data.frame(matrix(data = NA, nrow = 1, ncol = NC))
rain[1,1]<-PC_today[1,1]


# 
TA<-TA %>%
  filter(.,datetime>PC_starttime) #%>%

#Tmax for yesterday
Ttemp<-TA %>%
  filter(.,datetime<=PC_endtime) #%>%
Tmax<-data.frame(matrix(data = NA, nrow = 1, ncol = NC))
Tmax[1,1]<-PC_today[1,1]
Tmax[1,2:NC]<-99999 #To keep the numeric proterty
for(i in 2:NC){
  Tmax[,i]<-max(Ttemp[,i],na.rm=TRUE)
}

#######################################
#Tmin for yesterday 2019-08-19
#Ttemp<-TA %>%
#  filter(.,datetime<=PC_endtime) #%>%
Tmin_yesterday<-data.frame(matrix(data = NA, nrow = 1, ncol = NC))
Tmin_yesterday[1,1]<-PC_today[1,1]
Tmin_yesterday[1,2:NC]<-99999 #To keep the numeric proterty
for(i in 2:NC){
  Tmin_yesterday[,i]<-min(Ttemp[,i],na.rm=TRUE)
}
############################

#Tmin for today
Ttemp<-TA %>%
  filter(.,datetime>PC_endtime) %>%
  filter(.,datetime<=Tmin_endtime) 

Tmin<-data.frame(matrix(data = NA, nrow = 1, ncol = NC))
Tmin[1,1]<-PC_today[1,1]
Tmin[1,2:NC]<-99999 #To keep the numeric proterty
for(i in 2:NC){
  Tmin[,i]<-min(Ttemp[,i],na.rm=TRUE)
}



for (i in 2:NC){
  if(is.na(PC_today[1,i])|is.na(PC_yesterday[1,i])){
    rain[1,i]<-99999
  }else{
    rain[1,i]<-as.numeric(PC_today[1,i])-as.numeric(PC_yesterday[1,i])
    if(rain[1,i]>=999){rain[1,i]<-99999}
  }
  
  if(is.na(SW[1,i])){
    SW[1,i]<-99999
  }
  
  if(is.na(Tmax[1,i])|is.infinite(Tmax[1,i])){
    Tmax[1,i]<-99999
  }
##############################  
  if(is.na(Tmin_yesterday[1,i])|is.infinite(Tmin_yesterday[1,i])){
    Tmin_yesterday[1,i]<-99999
  }
################################  
  
  if(is.na(Tmin[1,i])|is.infinite(Tmin[1,i])){
    Tmin[1,i]<-99999
  }
  
}

colnames(SW)<-substr(colnames(SW),1,6)
colnames(SW)[1] <- "datetime"

data<-rbind(Tmax,Tmin,rain)
colnames(data)<-colnames(SW)

###
data_y<-Tmin_yesterday
colnames(data_y)<-colnames(SW)
tdata_y<-t(data_y)
tdata_y <- cbind(Row.Names = rownames(tdata_y), tdata_y)
# Delete the first row
tdata_y<-tdata_y[2:NC,]
tdata_y<-data.frame(tdata_y)
colnames(tdata_y)<-c("site","MINT_yesterday")
# Add a time column
DATE<-data.frame(matrix(data = NA, nrow = (NC-1), ncol = 1))
colnames(DATE)<-"DATE"
DATE[1:(NC-1),1]<-PC_endtime
final_y<-cbind(tdata_y$site,DATE,tdata_y$MINT_yesterday)
colnames(final_y)<-c("site","DATE","MINT_yesterday")
###

data<-rbind(data,SW)
tdata<-t(data)
tdata <- cbind(Row.Names = rownames(tdata), tdata)
# Delete the first row
tdata<-tdata[2:NC,]
tdata<-data.frame(tdata)
colnames(tdata)<-c("site","MAXT","MINT","PC","SW")
# Add a time column
DATE<-data.frame(matrix(data = NA, nrow = (NC-1), ncol = 1))
colnames(DATE)<-"DATE"
DATE[1:(NC-1),1]<-PC_endtime
final<-cbind(tdata$site,DATE,tdata$MAXT,tdata$MINT,tdata$PC,tdata$SW)
colnames(final)<-c("site","DATE","MAXT","MINT","PC","SW")

#Are these two lines necessary?
#current_date<-Sys.Date()
current_date<-as.character(current_date)

rio::export(final,paste0(outputpath,"ASP_daily-",current_date,".csv"))

rio::export(final,paste0("E:/Shared/Real-time_Data/ASP_daily/","ASP_daily-",current_date,".csv"))

#Tmin yesterday
rio::export(final_y,paste0(outputpath,"ASP_daily-",current_date,"_yesterday.csv"))



