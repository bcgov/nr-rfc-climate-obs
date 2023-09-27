# Overview

Most of these docs are duplicates... [see this readme in cicd folder](../cicd/climateobs/readme.md)


Contains the slightly modified version of the `hourly_format.R` script that was originally
created by [@ChunChaoKuo]( https://github.com/ChunChaoKuo ), has been modified so that
the input directories to the script can be configured using the environment variable `F_WX_DATA_DIR`.

# Docker - FWX

To try to create a package with the same / similar env used during development a
renv/dockerfile and docker are used to install locked dependencies and create a
dockerimage that is cached to the github container registry in this repository.

## Build Docker Image

Build uses a two stage build, allowing for a final compressed image size of 156MB.
Pretty good considering the 'rocker/r-base' image is 852MB.

```
docker build -f r_py_data_prep.Dockerfile -t rdataprep .
```

## Run Docker Image

The image by default is going to look for the previous day's data, so the python code
that aquires the data from hpfx needs to be run before this script.  (see scripts/python/main_fwx.py)

Once the expected data exists run:

```
docker run -e F_WX_DATA_DIR=/data/fwx -v /home/kjnether/rfc_proj/climate_obs/data:/data -it rdataprep Rscript hourly_format.R
```

# Docker - ZXS

The zxs build uses the [NRUtil.NRObjStoreUtil](https://github.com/bcgov/nr-objectstore-util)
module which will install BOTO3.  To save space the docker build  uses a multistage
approach where stage one installs the requirements into a venv, then remove the
various files in boto3 that are not required by this container. The venv then
gets copied in second stage saving >50Mi of space in the image.

## Build

```
docker build -t justpy -f zxs_data_pull.Dockerfile .
```

## RUN

```
docker run  -it \
    --env ZXS_DATA_DIR=./tmp/zxs \
    --env OBJ_STORE_BUCKET=$OBJ_STORE_BUCKET \
    --env OBJ_STORE_SECRET=$OBJ_STORE_SECRET \
    --env OBJ_STORE_USER=$OBJ_STORE_USER \
    --env OBJ_STORE_HOST=$OBJ_STORE_HOST \
    --env DEFAULT_DAYS_FROM_PRESENT=0 \
     -v /home/kjnether/rfc_proj/climate_obs/tmp:/data  justpy \
    /app/run_zxs.sh
```






## Debug Container
```
docker run -e F_WX_DATA_DIR=/data/ -v /home/kjnether/rfc_proj/climate_obs/tmp:/data   -it --entrypoint /bin/bash rdataprep
```

Where `/home/kjnether/rfc_proj/climate_obs/tmp` is the path to where the data has been
downloaded to.


