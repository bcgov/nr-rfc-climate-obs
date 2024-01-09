:: This script contains commands used to push data up to object storage.

:: while in dev, this is the path to java (using for unzip function)
SET PATH=%PATH%;C:\Program Files\Java\jdk-17.0.2\bin


SET RCLONE_PATH_VAR=rclone-v1.64.0-windows-amd64
if not exist rclone.exe (

    if not exist rclone.zip (
        wget https://downloads.rclone.org/v1.64.0/%RCLONE_PATH_VAR%.zip -O rclone.zip
    ) else (
        rem file doesn't exist
    )
    jar -xvf rclone.zip
    copy %RCLONE_PATH_VAR%\rclone.exe rclone.exe
    rmdir /s /q %RCLONE_PATH_VAR%
)

:: create the rclone config file
echo [nrsobjstore] > rclone.config
echo type = s3 >> rclone.config
echo provider = Minio >> rclone.config
echo env_auth = false >> rclone.config
echo access_key_id = %OBJ_STORE_USER% >> rclone.config
echo secret_access_key = %OBJ_STORE_SECRET% >> rclone.config
echo region = us-east-1 >> rclone.config
echo endpoint = https://nrs.objectstore.gov.bc.ca:443 >> rclone.config

:: rclone config directory, assuming its in the current directory
:: this needs to be manually configured
set current_dir=%cd%
set RCLONE_CONFIG=%current_dir%\rclone.config

:: Get the current year
set current_year=%Date:~0,4%
echo current year is %current_year%

:: now perform the rclone syncs

:: ----- Sync the climate obs data spreadsheet
.\rclone.exe sync ^
    --check-first ^
    \\\\%SFP_HOST%\\%SFP_PATH_1%\\%SFP_PATH_2%\\Watershare\\RFC\\1DATA\\2CLIMATE_OBS\\%current_year% ^
    nrsobjstore:rfcdata\\models\\data\\climate_obs

:: Sync the hourly ECC data
.\rclone.exe sync ^
    --check-first ^
    nrsobjstore:rfcdata\\RFC_DATA\\ECCC\\hourly\\csv ^
    \\\\%SFP_HOST_DATA_1%\\Shared\\MPOML\\HOURLY\\csv

:: RFC_DATA/ECCC/hourly/csv to \\sewer\shared\MPOML\HOURLY\csv
:: \\sewer\Shared\MPOML\HOURLY\csv
:: delete the rclone config
del rclone.config



