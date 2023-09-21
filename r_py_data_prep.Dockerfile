
# seeing if I can setup a job with python and r
FROM rhub/r-minimal:4.2.3 as STAGE1

WORKDIR /app

# copy the r script and lock file so renv can be built
COPY ["./scripts/r/hourly_format.R", \
      "./renv.lock", \
      "/app/"]

# install the build tools
RUN apk update
RUN apk add --update alpine-sdk \
        libcurl curl curl-dev libxml2 libxml2-dev

## create directories
RUN R -e "install.packages('renv',version = '0.17.3', repos = 'https://cloud.r-project.org')" && \
    R -e "renv::init(bare=TRUE) ; renv::restore() ; renv::isolate()"

# copy renv to minimal without the dev tools to save space
FROM rhub/r-minimal:4.2.3
WORKDIR /app

# copy the r script
COPY ["./scripts/r/hourly_format.R", \
      "./renv.lock", \
      "scripts/python/requirements.txt", \
      "scripts/python/logging.config", \
      "scripts/python/main_fwx.py", \
      "scripts/python/remote_ostore_sync.py", \
      "scripts/python/main_zxs.py", \
      "scripts/python/main_asp.py", \
      "/app/"]

# copy the renv files
COPY --from=STAGE1 /app/renv /app/renv
COPY --from=STAGE1 ["/app/renv.lock", "/app/.Rprofile", "/app/"]

ENV PYTHONUNBUFFERED=1
RUN apk add libxml2 && \
    R -e "install.packages('renv', version = '0.17.3', repos = 'https://cloud.r-project.org')" && \
    apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python && \
    python3 -m ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools && \
    pip install -r requirements.txt
