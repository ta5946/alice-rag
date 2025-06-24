---
sort: 2
title: CCDB
---

# CCDB

As many of the `O2` executables, also the simulation depends heavily on the CCDB to retrieve configurations, meta information or objects required during the run.

## Prerequisites

A valid GRID **token** must be present, see [here](../gettingstarted/README.md#alien-grid-token)

## CCDB snapshots

During the execution of the simulation workflow, different tasks need CCDB objects. The simulation of different timeframes is parallelised so there are multiple tasks that require the same objects. This is one reason why we use **snapshots**:
When an object is requested for the first time, it os downloaded and **cached** so that following requests can be redirected to that chached object instead of querying the CCDB again.
By default the cache directory is `${CWD}/ccdb` but it can be changed by
```bash
export ALICEO2_CCDB_LOCALCACHE=/path/to/snapshot_cache
```
**NOTE**: Make sure to set this to an absolute path.

This mechanism can also be useful to run a simulation without the need to access the CCDB at all: Simply refer to or copy a snapshot directory from a previous simulation run to the directory you are running the current simulation in.

**NOTE**: No check is done on whether the timestamp of your simulation corresponds to the cached objects; they will simply be used as-is and are only identified by their path.

## Use custom objects/snapshots

Using the caching mechanism is not only useful to avoid redundant queries to the CCDB but it can also be used to inject custom objects into your workflow that would otherwise be fetched based on the timestamp.
As an example, you might be interested in some specific alignment at a given timestamp `<timestamp>`. As said before, that might not coincide with the timestamp of the simulation itself.
So let's assume your cache directory is at `${ALICEO2_CCDB_LOCALCACHE}` and another specific alignment should be take for TPC. Before starting the simulation, run
```bash
${O2_ROOT}/bin/o2-ccdb-downloadccdbfile --host http://alice-ccdb.cern.ch -p TPC/Calib/Align --timestamp <timestamp> -d ${ALICEO2_CCDB_LOCALCACHE}
```
Now, you are good to run the simulation and the desired TPC alignment will be used.
