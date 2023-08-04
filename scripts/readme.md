# Overview

Contains the slightly modified version of the `hourly_format.R` script that was originally
created by [@ChunChaoKuo]( https://github.com/ChunChaoKuo ), has been modified so that
the input directories to the script can be configured using the environment variable `F_WX_DATA_DIR`.

# Docker

To try to create a package with the same / similar env used during development a
renv/dockerfile and docker are used to install locked dependencies and create a
dockerimage that is cached to the github container registry in this repository.

## Build Docker Image

Build uses a two stage build, allowing for a final compressed image size of 156MB.
Pretty good considering the 'rocker/r-base' image is 852MB.

```
docker build -f r_data_prep.Dockerfile -t rdataprep .
```

## Run Docker Image

The image by default is going to look for the previous day's data, so the python code
that aquires the data from hpfx needs to be run before this script.  (see scripts/python/main_fwx.py)

Once the expected data exists run:

```
docker run -e F_WX_DATA_DIR=/data/ -v /home/kjnether/rfc_proj/climate_obs/tmp:/data -it rdataprep
```



## Debug Container
```
docker run -e F_WX_DATA_DIR=/data/ -v /home/kjnether/rfc_proj/climate_obs/tmp:/data   -it --entrypoint /bin/bash rdataprep
```

Where `/home/kjnether/rfc_proj/climate_obs/tmp` is the path to where the data has been
downloaded to.


