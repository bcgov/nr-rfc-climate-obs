## Overview

This repo will be used to build / transition the existing data pipeline that aquire and 
transform climate observation data for use in hydrological modelling.

The existing data pipeline is using [mermaid](https://mermaid.js.org/) here [documented here:](./data_description.mmd)

It consists of windows scheduler jobs that call .bat files which do one of the following:
* pull data using `wget` from remote sources
* .bat file wrappers to other scripts (R)
* some scripts are related to one another loosly based inputs / outputs and staggered execution schedules

