---
sort: 3
title: Detector geometry
---

# Detector geometry

Each module consists of several (mostly quite a lot) of volumes. Each volume has a certain medium assigned which defines the volumes physical properties (steel, air, vacuum, concrete a custom mixture and so forth).

## Inspecting the geometry

A simulation run dumps the used geometry at `<prefix>_geometry.root`. This file can be browsed using ROOT, volumes can be drawn etc. For instance, to draw the geometry as-is, do
```cpp
auto geoMgr = TGeoManager::Import("<prefix>_geometry.root");
geoMgr->GetTopVolume()->Draw();
```

This can of course also be done in an interactive ROOT session.

## Material densities

Material densities can be changed at runtime from the outside. There is a global setting as well as a setting **per module**.
The local settings take precedence over the global setting.
The default for all parameters is `1`.

To scale the overall density of the geometry by a factor 2, for instance, run the simulation with
```bash
o2-sim <args> --configKeyValues "SimMaterialParams.globalDensityFactor=2"
```

To scale densities per module, on can do so for instance for the TPC and ITS by running the simulation like
```bash
o2-sim <args> --configKeyValues "SimMaterialParams.localDensityFactor=ITS:1.5,TPC:1.2"
```


## Medium properties

As mentioned, a medium defines the physical properties of a volume. Some of them can be changed at runtime as shown in the following.

### Energy thresholds

When a particle traverses the detector, a certain interaction with the material (also called physics process) can lead to the production of secondary particles.
In reality, all of those particles would be produced, however, in simulation one has the possibility to suppress the production of particles below a certain energy threshold. The following cut parameters are available:
* `CUTGAM`: gammas,
* `CUTELE`: electrons,
* `CUTNEU`: neutral hadrons,
* `CUTHAD`: charged hadrons,
* `CUTMUO`: muons,
* `BCUTE`: electron bremsstrahlung,
* `BCUTM`: muon and hadron bremsstrahlung,
* `DCUTE`: delta-rays by electrons,
* `DCUTM`: delta-rays by muons,
* `PPCUTM`: direct pair production by muons.

They are set globally [here](https://github.com/AliceO2Group/AliceO2/blob/dev/Detectors/gconfig/src/SetCuts.cxx).

It is possible to set specific parameters for each medium. For most modules, there exists a text file which is parsed at runtime. As an example, the files for the passive modules are [here](https://github.com/AliceO2Group/AliceO2/tree/dev/Detectors/Passive/data).

It is also possible to change parameters on the fly. To do so, first extract a JSON file with all current parameters.
```bash
o2-sim-serial -n0 --configKeyValues "MaterialManagerParam.outputFile=o2_medium_params.json"
```
This will leave you with the `o2_medium_params.json`. It contains all media per module and the parameters in there can be set by the user. A new parameter configuration is injected with
```bash
o2-sim --configKeyValues "MaterialManagerParam.inputFile=o2_medium_params_modified.json" [<further_arguments>]
```

### Special controls

Some physics processes can be switched on or off. The global default settings are [here](https://github.com/AliceO2Group/AliceO2/blob/dev/Detectors/gconfig/src/SetCuts.cxx).

In the same way as the energy thresholds, they can also be tweaked at runtime by manipulating a `o2_medium_params.json` and re-inject it.

**IMPORTANT NOTE**: At the moment, any local changes on the special controls per medium take no effect when using Geant4. Only the **global settings** will affect the behaviour of the transport code


## Magnetic field

**...under construction...**
