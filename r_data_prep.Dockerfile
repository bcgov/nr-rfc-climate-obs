FROM rhub/r-minimal:4.5.0 as STAGE1

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
FROM rhub/r-minimal:4.5.0
WORKDIR /app

# copy the r script
COPY ["./scripts/r/hourly_format.R", \
      "./renv.lock", \
      "/app/"]

# copy the renv files
COPY --from=STAGE1 /app/renv /app/renv
COPY --from=STAGE1 ["/app/renv.lock", "/app/.Rprofile", "/app/"]

RUN R -e "install.packages('renv', version = '0.17.3', repos = 'https://cloud.r-project.org')"

ENTRYPOINT [ "Rscript", "hourly_format.R"]
