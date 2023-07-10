[![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)](<Redirect-URL>)

# nr-rfc-climate-obs

Work related to re-building the climate observations data pipeline so that it can 
run in a variety of different environments.

Objective is to move as much of the existing R code as possible with minimal changes.

The general architectural pivot is moving away from using Shared File and Print (SFP)
to using object storage for persistence of artifacts created by different data 
aquisition / processing scripts.

# Contents:

    * [overview of existing data processing pipeline](./docs/background.md)
    * [mermaid docs of existing pipeline](./docs/data_description.mmd)
    

