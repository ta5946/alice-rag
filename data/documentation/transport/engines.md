---
sort: 1
title: Transport engines
---

# Transport engines

## GEANT4

### Scaling hadronic cross sections

Hadronic cross sections can be scaled by passing a specific Geant4 configuration to the transport simulation.
[This is an example](https://github.com/AliceO2Group/O2DPG/blob/eb3591632fe75ba65ff68353984839c22826a89c/MC/config/PWGLF/xsection/g4config_had_x2.in#L66-L72) where various hadronic cross sections are scaled.

## FLUKA

Informtation about FLUKA.

## GEANT3

Information about GEANT3.

## MCReplay engine

The MCReplay engine can be used to replay a simulation based on steps logged by the [MCStepLogger](../mcsteplogger/). It is therefore not actually a simulation engine but only mimics one. It simply injects each step, one after the other, from a previous simulation.

To run it, first follow the steps as explained in [MCStepLogger](../mcsteplogger/) to produce a file containing logged steps. To then replay them, do
```bash
o2-sim-serial -n <ref_nevents> -e MCReplay -g extkinO2 --extKinFile o2sim_Kine.root -o replay
```
Note that it will look for the recorded steps in the same directory, trying to find `MCStepLoggerOutput.root`. If the name or the path of the step log file is different, it can be passed with `--configKeyValues="MCReplayParam.stepFilename=<path/step/file/name>"`.

It is advisory to at least use another output prefix as done in this case (`-o replay`) since otherwise the previous output files might be overwritten. Or simply run in a different directory.

It is also possible to set a minimum energy cut (in units of GeV) that particles at least have to have when produced. To do so, use `--configKeyValues="MCReplayParam.energyCut=0.1"` if everything produced below `0.1 GeV` should be dropped.

Energy cuts can also be set per simulation medium and type. **More information on this will be added shortly.**

### Important remarks

Make sure to use/exclude the same modules as used in the reference run (`-m` and `--skipModules` flags, see [here](README.md/#simulation-geometry-modules-and-detectors)).

It is of course not possible to simulate more events than those simulated during the step logging.

### Use cases

Comparing the produced hits with those from the reference run it is possible to omit steps/particle production which have a negligible impact on the hits and hence on digits. As a result, the detector simulation can be tuned to be faster and more efficient.

## O2TrivialMCEngine

This engine is not an actual engine but it serves as a kind of placeholder for scenarios in which no real engine is needed. Currently, there is one particular use case which is when only the [kinematics](mckine.md) of primaries is of interest. Such a run is typically initiated with
```bash
o2-sim --noGeant
```
It is indeed not necessary to explicitly specify the engine, it is set automatically.

**...under construction...**
