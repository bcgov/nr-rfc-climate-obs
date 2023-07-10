# Ideas

A place to write down random thoughts with respect to how to re-implement/re-architect
the existing data pipeline.

### Data Storage format pivot

Instead of loading data into xl for climate obs / other???
Store the data in parket of other data science formats.  
* more efficient formats for size and time required to open and read.

### Input / output data configuration

* Describe inputs / outputs to scripts external to script.
    * explore whether we could store in mermaid files, have
      scripts consume the mermaid files
    * with this scenario docs and config would be the same thing
    * investigate using mermaid format to accomplish this.