# Overview

## Existing State

This repo will be used to build / transition the existing data pipeline that aquire and
transform climate observation data for use in hydrological modelling.

The following is a diagram of the existing data pipeline that runs on a VM / on prem.
[mermaid](https://mermaid.js.org/) and this is further
[documented here:](./data_description.mmd)

It consists of windows scheduler jobs that call .bat files which do one of the following:
* pull data using `wget` from remote sources
* .bat file wrappers to other scripts (R)
* some scripts are related to one another loosly based inputs / outputs and staggered
  execution schedules

## Planned State

### Data

Migrate the official location of the data from on prem / mounted shared storage to
object storage.

### Processing

Migrate the processing from R scripts to python scripts in containers.  Configure these
processes so they are portable.  Current target is to run either as github actions or
as kubernetes cronjobs.  Current preference is to run as kubernetes cron jobs as the
bcgov org in github is restricted to 20 runners, which are currently starting to be over
allocated resulting in longer than normal waits for jobs to innitiate.

All kubernetes jobs will be setup with automated deployments using helm.


