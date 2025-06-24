---
sort: 2
title: Transport
---

# Transport

The detector simulation is triggered with
```bash
o2-sim <args>
```

The simulation creates the following output files:

| File                      | Description                                                                            |
|---------------------------|----------------------------------------------------------------------------------------|
| `o2sim_Kine.root`         | contains kinematics information (primaries and secondaries) and event meta information |
| `o2sim_geometry.root`     | contains the final ROOT geometry created for simulation run                            |
| `o2sim_grp.root`          | special global run parameters (grp) such as field                                      |
| `o2sim_XXXHits.root`      | hit file for each participating active detector XXX                                    |
| `o2sim_configuration.ini` | summary of parameter values with which the simulation was done                         |
| `o2sim_serverlog`         | log file produced from the particle generator server                                   |
| `o2sim_workerlog0`        | log file produced form the transportation processes                                    |
| `o2sim_hitmergerlog`      | log file produced from the IO process                                                  |


## Main command line options

The following options are available:

| Option                                         | Description                                                                                                                                                                                                                             |
|------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-h [ --help ]`                                | Prints the list of possible command line options and their default values.                                                                                                                                                              |
| `-e [ --mcEngine ] arg (=TGeant4)`             | VMC backend to be used. TGeant3 or TGeant4. See [transport section](../transport/)                                                                                                                                                      |
| `-g [ --generator ] arg (=boxgen)`             | Event generator to be used. See [generators section](../generators/)                                                                                                                                                                    |
| `-t [ --trigger ] arg`                         | Event generator trigger to be used. See [trigger section](../generators/trigger.md)                                                                                                                                                     |
| `-m [ --modules ] arg (=all modules)`          | List of modules/geometries to include (default is ALL); example -m PIPE ITS TPC                                                                                                                                                         |
| `--skipModules arg`                            | list of modules excluded in geometry (precedence over -m) See [transport section](../transport/)                                                                                                                                        |
| `--readoutDetectors arg`                       | list of detectors creating hits, all if not given; added to to active modules. See [transport section](../transport/)                                                                                                                   |
| `--skipReadoutDetectors arg`                   | list of detectors to skip hit creation (precedence over --readoutDetectors). See [transport section](../transport/)                                                                                                                     |
| `-n [ --nEvents ] arg (=0)`                    | number of events                                                                                                                                                                                                                        |
| `--startEvent arg (=0)`                        | index of first event to be used (when applicable, e.g. for `hepmc` generator). See [generators section](../generators/)                                                                                                                 |
| `--extKinFile arg (=Kinematics.root)`          | name of kinematics file for event generator from file (when applicable). See [generators section](../generators/)                                                                                                                       |
| `--embedIntoFile arg`                          | filename containing the reference events to be used for the embedding                                                                                                                                                                   |
| `-b [ --bMax ] arg (=0)`                       | maximum value for impact parameter sampling (when applicable)                                                                                                                                                                           |
| `--isMT arg (=0)`                              | multi-threaded mode (Geant4 only)                                                                                                                                                                                                       |
| `-o [ --outPrefix ] arg (=o2sim)`              | prefix of output files                                                                                                                                                                                                                  |
| `--logseverity arg (=INFO)`                    | severity level for FairLogger                                                                                                                                                                                                           |
| `--logverbosity arg (=medium)`                 | level of verbosity for FairLogger (low, medium, high, veryhigh)                                                                                                                                                                         |
| `--configKeyValues`                            | Like `--configFile` but allowing to set parameters on the command line as a string sequence. Example `--configKeyValues "Stack.pruneKine=false"`. Takes precedence over `--configFile`. Parameters need to be known ConfigurableParams. |
| `--configFile arg`                             | Path to an INI or JSON configuration file                                                                                                                                                                                               |
| `--chunkSize arg (=500)`                       | max size of primary chunk (subevent) distributed by server                                                                                                                                                                              |
| `--chunkSizeI arg (=-1)`                       | internalChunkSize                                                                                                                                                                                                                       |
| `--seed arg (=0)`                              | initial seed as ULong_t (default: 0 == random)                                                                                                                                                                                          |
| `--field arg (=-5)`                            | L3 field rounded to kGauss, allowed values +-2,+-5 and 0; +-<intKGaus>U for uniform field; "ccdb" for taking it from CCDB                                                                                                               |
| `-j [ --nworkers ] arg (=4)`                   | number of parallel simulation workers (only for parallel mode)                                                                                                                                                                          |
| `--noemptyevents`                              | only writes events with at least one hit                                                                                                                                                                                                |
| `--CCDBUrl arg (=<http://alice-ccdb.cern.ch)>` | URL for CCDB to be used.                                                                                                                                                                                                                |
| `--timestamp arg`                              | global timestamp value in ms (for anchoring) - default is now ... or beginning of run if ALICE run number was given                                                                                                                     |
| `--run arg (=-1)`                              | ALICE run number                                                                                                                                                                                                                        |
| `--asservice arg (=0)`                         | run in service/server mode                                                                                                                                                                                                              |
| `--noGeant`                                    | prohibits any Geant transport/physics                                                                                                                                                                                                   |
| `--forwardKine`                                | forward kinematics on a FairMQ channel                                                                                                                                                                                                  |
| `--noDiscOutput`                               | switch off writing sim results to disc (useful in combination with forwardKine)                                                                                                                                                         |
| `--fromCollContext arg`                        | Use a pregenerated collision context to infer number of events to simulate, how to embedd them, the vertex position etc. Takes precedence of other options such as "--nEvents".                                                         |

There is further documentation on [generators](../generators/) and [transport engines](../transport/engines.md). For module and detector composition, please see [below](#simulation-geometry-modules-and-detectors).

## Expert control via environment variables

`o2-sim` is sensitive to the following environment variables:

| Variable              | Description                                                                                                                        |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `ALICE_O2SIM_DUMPLOG` | When set, the output of all FairMQ components will be shown on the screen and can be piped into a user logfile.                    |
| `ALICE_NOSIMSHM`      | When set, communication between simulation processes will not happen using a shared memory mechanism but using ROOT serialization. |

## Configurable Parameters

Simulation makes use of `configurable parameters` as described in the [ConfigurableParam.md](https://github.com/AliceO2Group/AliceO2/blob/dev/Common/SimConfig/doc/ConfigurableParam.md) documentation.
Detector code as well as general simulation code declare such parameter and access them during runtime.
Once a parameter is declared, it can be influenced/set from the outside via configuration files or from the command line. See the `--configFile` as well as `--configKeyValues` command line options.
The complete list of parameters and their default values can be inspected in the file `o2sim_configuration.ini` that is produced by an empty run `o2-sim -n 0 -m CAVE`.

Important parameters influencing the transport simulation are:

| Main parameter key | Description                                                                                                                                  |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `G4`               | Parameters influencing the Geant4 engine, such as the physics list. Example "G4.physicsmode=kFTFP_BERT_optical_biasing"                      |
| `Stack`            | Parameters influencing the particle stack. Example include whether the stack does kinematics pruning or whether it keeps secondaries at all. |
| `SimCutParams`     | Parameters allowing to set some sime geometry stepping cuts in R, Z, etc.                                                                    |
| `Diamond`          | Parameter allowing to set the interaction vertex location and the spread/width. Is used in all event generators.                             |
| `Pythia6`          | Parameters that influence the pythia6 generator.                                                                                             |
| `Pythia8`          | Parameters that influence the pythia8 generator.                                                                                             |
| `HepMC`            | Parameters that influence the HepMC generator.                                                                                               |
| `TriggerParticle`  | Parameters influencing the trigger mechanism in particle generators.                                                                         |


## Simulation geometry, modules and detectors

In simulation we call a **"module"** of the ALICE experiment a coherent object assembled from various smaller volumes. It has a well-defined purpose and can - in principle - be installed and operated without any other module. There is an important difference between simulation and the real experiment:
In simulation, modules can be completely taken out anytime so that they do not add to the overall material budget. On the other hand, that is not possible in the experiment.
The entirety of all modules (usually embedded in a so-called "world volume") yields the simulation geometry.
Particles traversing a module, depending on their type, location and momentum, might deposit energy in the material.
A **"detector"** in the simulation context is a special module in that it has sensitive volumes that can register these energy deposits. In simulation, the energy deposits are called "hits".
All modules that are not detectors are also called **"passive modules"**.

By default, `o2-sim` runs a simulation with the complete Run3 geometry. Modules can be excluded from the geometry using the `--skipModules <mod1> [<mod2> [...]]`. In that case they do not contribute to the overall material budget in the simulation. If only certain modules should be included, one uses `-m|--modules <mod1> [<mod2> [...]]`. Note that `--skipModules` takes precedence over `-m`.

By default, all detectors produce hits and are therefore considered read-out. The detectors' readout can be switched off with `--skipReadoutDetectors <det1> [<det2> []]`. Reading out only a certain subset of detectors is achieved with `-readoutDetectors <det1> [<det2> [...]]`. Note that `--skipReadoutDetectors` takes precedence over `--readoutDetectors`. No matter what the readout options are:
If a detector is in the list of modules, its material will contribute to the overall geometry and therefore material budget. However, these options are useful to safe time and resources if one is only interested in the readout of certain detectors.
The header files of all passive module and their geometry description can be found [here](https://github.com/AliceO2Group/AliceO2/tree/dev/Detectors/Passive/include/DetectorsPassive) while the detectors are described [here](https://github.com/AliceO2Group/AliceO2/tree/dev/Detectors).
In the latter case the overall file structure is more complex and usually, the geometry description is in some `simulation` sub-directory. O2 has its special [base class for detectors](https://github.com/AliceO2Group/AliceO2/blob/dev/Detectors/Base/include/DetectorsBase/Detector.h).

### Available Run3 modules

The detector names are [centrally defined](https://github.com/AliceO2Group/AliceO2/blob/dev/DataFormats/Detectors/Common/include/DetectorsCommonDataFormats/DetID.h). Any of those can be passed to the `--redoutDetectors` and `-m` options (as well as their corresponding `--skip` counter part).

Passive modules are not yet centrally defined. Currently there are
* `HALL`: the experimental cavern,
* `MAG`: the L3 magnet,
* `PIPE`: the beampipe,
* `ABSO`: the absorber,
* `DIPO`: the dipole magnet,
* `COMP`: the compensator in very forward region,
* `SHIL`: the shield to filter muons.

The modules for the ALICE Run5 developments are descried [here](run5.md).

**..under construction...**

{% include list.liquid all=true %}
