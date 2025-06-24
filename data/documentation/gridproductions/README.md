---
sort: 6
title: MC GRID productions
---

# MC GRID productions

In order to collect enough statistics, Monte Carlo simulations typically need to be spread out and run on large compute farms.
For this, we use the Worldwide LHC Computing Grid (WLCG) <https://wlcg.web.cern.ch/> by default, which in rough terms collects compute farms into an collaborative abstract layer to which compute jobs can be submitted.

The ALICE interface to this system is called AliEn <https://jalien.docs.cern.ch/>.


A few ways exist to make use of the GRID computing power for simulation:

## Official (large scale) productions

Official productions for ALICE physics working groups or larger productions for research and development
(detector groups, etc.) should be handled via the Data Processing Group (DPG).

A ticket with type "Production Request" should be created in [JIRA](https://alice.its.cern.ch/jira/projects/O2), explaining the purpose, the setup, the software version to be used and so on. The production will then be orchestrated by the DPG production manager.
Note that a ticket is also needed for test requests, no mail requests will be accepted.

Productions may need to be approved by the Physics Board depending on resource usage.
The CPU limit for tests or productions without Physics board approval is 1d@10kCPUs.

## Personal (development or test) productions

Each member of the ALICE collaboration has a personal compute quota and one can submit jobs spanning
O(100) CPUs for development and testing cycles which is a considerable resource pool.

Here, one needs to create a JDL file describing the job, upload executables to the GRID and use a a tool like `alien.py` to interact
with the GRID services. Documentation can be found [here](https://jalien.docs.cern.ch/), with the JDL job reference available [here](https://alien.web.cern.ch/content/documentation/howto/user/jobs).

The process of setting up JDLs and copying necessary files can be cumbersome.
For this reason, there exists also a [tool](https://github.com/AliceO2Group/O2DPG/blob/master/GRID/utils/grid_submit.sh), called `grid_submit.sh`
which allows to submit a locally existing script to run on the GRID without much boilerplate. The tool is work-in-progress and needs more generalizations but may be a good starting point.

### Configuring `grid_submit.sh`

* To alter the TTL setting of your job, pass `--ttl <ttl>`.
* If your local user name from where you submit do not coincide, use `--asuser <alien-user>` to set your GRID user name.
* Production MC simulations are run in `SPLITs`. More explanation on that is provided [here](../o2dpgworkflow/anchored.md). Use `--prodsplit <prodsplit>` to alter the number of splits; default is `1`.

### Important note

It is highly recommended, if possible, to test custom developments or new implementations first locally or on `lxplus` before moving to the GRID.
Among other things the advantages could be:

* no waste of GRID quota,
* all artifacts like ROOT or log files are available (some might be missing if you forget or have wrong/incomplete output specifications in the JDL for the GRID run),
* easy access and inspections, no downloads/uploads,
* depending on the complexity, maybe as fast or even faster than GRID testing (no waiting time, no additional saving time),
* easier to reconfigure, run again, change code, run again etc.

{% include list.liquid all=true %}
