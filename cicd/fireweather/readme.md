# deployment notes


## Docker

### build image - local

```
docker build -f r_py_data_prep.Dockerfile -t r_py .
```

### Run image - local

load the environment variables from .env file, or modify calls here so
they are provided to the docker run command.

```
docker run   \
--env F_WX_DATA_DIR=/data \
--env RENV_PATHS_ROOT=/data/renvcache \
--env OBJ_STORE_BUCKET=$OBJ_STORE_BUCKET \
--env OBJ_STORE_SECRET=$OBJ_STORE_SECRET \
--env OBJ_STORE_USER=$OBJ_STORE_USER \
--env OBJ_STORE_HOST=$OBJ_STORE_HOST \
-v /home/kjnether/rfc_proj/climate_obs/tmp:/data \
-t r_py /bin/bash -c "python main_fwx.py && Rscript hourly_format.R"
```

### pull and test image from github

Should be the same image as the one built locally, but when things stop working
it can be useful to pull a specific image and test it locally.

First identify which image to pull from here:
https://github.com/bcgov/nr-rfc-climate-obs/pkgs/container/firedata_pipe

example of pulling image with the tag 20230801-1651

```
docker pull ghcr.io/bcgov/firedata_pipe:20230801-1651
```

finnally running that image locally

```
docker run   \
--env F_WX_DATA_DIR=/data \
--env RENV_PATHS_ROOT=/data/renvcache \
--env OBJ_STORE_BUCKET=$OBJ_STORE_BUCKET \
--env OBJ_STORE_SECRET=$OBJ_STORE_SECRET \
--env OBJ_STORE_USER=$OBJ_STORE_USER \
--env OBJ_STORE_HOST=$OBJ_STORE_HOST \
-v /home/kjnether/rfc_proj/climate_obs/tmp:/data \
-t ghcr.io/bcgov/firedata_pipe:20230801-1651 /bin/bash -c "python main_fwx.py && Rscript hourly_format.R"
```
# Openshift Deployment
## Helm Chart - Deploy to openshift

running the helm chart

create the following env vars:

* OBJ_STORE_BUCKET
* OBJ_STORE_SECRET
* OBJ_STORE_USER
* OBJ_STORE_HOST

```
helm upgrade --install \
--set obj_store.bucket=$OBJ_STORE_BUCKET \
--set obj_store.secret=$OBJ_STORE_SECRET \
--set obj_store.user_id=$OBJ_STORE_USER \
--set obj_store.host=$OBJ_STORE_HOST \
--set fire_data_job.fire_data_mnt_point=/data \
fireweather \
fireweather
```

## Initiate a manual run of the cronjob

The cronjob is configured to run on a schedule, when testing you can initiate
the job using this command.

```
oc create job --from=cronjob/fire-data-acquisition-job "fire-data-manual-run-$(date +%s)"
```

Then monitor job via openshift console.

Finally clean up the job
```
oc get jobs
oc delete jobs <job name>
```
