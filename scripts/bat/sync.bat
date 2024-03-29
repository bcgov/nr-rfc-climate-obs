:: This script contains commands used to push data from on prem servers to object
:: storage.

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
    \\Sfp.idir.bcgov\s164\S63101\Watershare\RFC\1DATA\2CLIMATE_OBS\%current_year% ^
    nrsobjstore:rfcdata\models\data\climate_obs







