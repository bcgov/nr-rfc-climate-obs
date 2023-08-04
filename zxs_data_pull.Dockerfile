FROM python:3.11.4-alpine as build
WORKDIR /app
COPY ["scripts/python/requirements.txt", \
      "/app/"]
RUN python3 -m ensurepip && \
      pip3 install --no-cache --upgrade pip setuptools && \
      python3 -m venv venv && \
      . venv/bin/activate && \
      pip install -r requirements.txt && \
      # botocore is a beast... deleting a bunch of stuff we don't need
      mkdir tmp && \
      cp venv/lib/python3.11/site-packages/botocore/data/*.json tmp/ && \
      cp -r venv/lib/python3.11/site-packages/botocore/data/s3* tmp/ && \
      rm -rf venv/lib/python3.11/site-packages/botocore/data/* && \
      cp -r tmp/* venv/lib/python3.11/site-packages/botocore/data && \
      rm -rf tmp

FROM python:3.11.4-alpine
WORKDIR /app
COPY --from=build /app/venv /app/venv
COPY ["scripts/python/logging.config", \
      "scripts/python/main_fwx.py", \
      "scripts/python/main_zxs.py", \
      "scripts/python/remote_ostore_sync.py", \
      "/app/"]

RUN mkdir -p /app/tmp && apk update && \
python3 -m ensurepip && \
pip3 install --no-cache --upgrade pip && \
. venv/bin/activate




# pretty big image... boto is a beast... don't need it, so can install deps in venv
# in one stage, then copy that venv and activate it in a second stage.
# some ideas https://pythonspeed.com/articles/multi-stage-docker-python/
# docker run  -it --env F_WX_DATA_DIR=/data -v /home/kjnether/rfc_proj/climate_obs/tmp:/data --entrypoint "/bin/bash" ghcr.io/bcgov/firedata_pipe:20230731-2220
# # docker run  -it --env ZXS_DATA_DIR=/data/zxs -v /home/kjnether/rfc_proj/climate_obs/tmp:/data --entrypoint "/bin/bash" justpy