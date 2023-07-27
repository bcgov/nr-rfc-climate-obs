# Overview

Trying to figure out a way to define a re-produceable environment for the R installs
so that the dependencies get declared, and can therefor be re-installed in an easily
reproduceable way.

Using the package renv which seems to solve the issue.

[Docs on Renv](https://ecorepsci.github.io/reproducible-science/renv.html#usage)


# Install Dependencies using Lock File

First make sure renv package is installed, and if not then install it
`install.packages("renv")`

Next assuming the lock file

```
R
renv::init(bare=TRUE)
renv::restore(prompt=FALSE)

# not sure why, but shiny doesn't seem to get added to the lock file
# and as such restoring from the lock file does not result in shiny
# being installed into the env.

install.packages('shiny')
renv::snapshot()
q(save='yes')

```

# Install Dependencies using renv - NET NEW ENV

Creating a net new environment.  This is only required for starting from scratch if
there are problems installing from the lock file.

```
R
renv::init()
install.packages('shiny')
```

# Run the R-Shiny App

``` R
R
library(shiny)
shiny::runApp("./RDataImport/QC_Shiny_Climate")
```

# Issues Encountered

The following is a snip from the logs when tried to install in WSL (Ubunbu 20.04).
tried a number of things to get the packages to compile with no success.  In the
end just upgraded to 22.04 and then everything installed easily.

```
The following package(s) were not installed successfully:
        [sf]: package 'MASS' is not available
        [bcmaps]: package 'lattice' is not available
        [rio]: package 'foreign' is not available
        [terra]: install of package 'terra' failed [error code 1]
        [nlme]: install of package 'nlme' failed [error code 1]
        [lmtest]: install of package 'lmtest' failed [error code 1]
        [quadprog]: install of package 'quadprog' failed [error code 1]
        [tseries]: install of package 'tseries' failed [error code 1]
        [urca]: install of package 'urca' failed [error code 1]
        [forecast]: install of package 'forecast' failed [error code 1]
        [imputeTS]: install of package 'imputeTS' failed [error code 1]

```

