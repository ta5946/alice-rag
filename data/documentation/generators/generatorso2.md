---
sort: 1
title: Generators implemented in O2
---

# Generators implemented in O2

There are several generators which can be directly specified with `o2-sim -g <generator>` which are summarised in the following. In some cases, as you will see below, there is the need of setting addition parameters via `--configKeyValues`. Furthermore, there might be additional optional parameters that can be passed via `--configKeyValues`.

## Pythia8

Pythia8 is the default generator for ALICE Run3, and the only one with a native interface in the O2 codebase, via the [GeneratorPythia8](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/GeneratorPythia8.h) class.

For Pythia8 there are 5 different options/values which can be directly used as `<generator>` in `o2-sim -g <generator>`:

### pythia8

This selects Pythia8 as the generator for simulation but it is necessary to pass a Pythia8 configuration file, such as
```text
### beams
Beams:idA 2212			# proton
Beams:idB 2212 			# proton
Beams:eCM 14000. 		# GeV

### processes
SoftQCD:inelastic on		# all inelastic processes

### decays
ParticleDecays:limitTau0 on	
ParticleDecays:tau0Max 10.
```
which configures the Pythia8 instance.

Passing of this configuration file happens via the configurable parameter `GeneratorPythia8`. In the simplest case, one may just use `--configKeyValues "GeneratorPythia8.config=<path/to/config>"`.

Next to allowing to specify the configuration file, the configurable parameter "GeneratorPythia8" (source definition [here](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/GeneratorPythia8Param.h)) has more options that allow to configure the Pythia8 instance in O2. The important keys are defined in the corresponding class

* `config` : specification of the Pythia8 configuration file
* `includePartonEvent = [true|false]` : whether we keep the partonic part of the event or filter it out (default false) 
* `hooksFileName` : string to specify a ROOT macro file containing a trigger function (optional)
* `hooksFuncName` : string to specify the functionname corresponding to the trigger function (optional)


### pythia8pp

A special, pre-configured case of `<pythia8>` for pp collisions. This uses default Pythia8 with [this configuration](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/share/egconfig/pythia8_inel.cfg).

### pythia8hf

A special, pre-configured case of `<pythia8>` for HF. This uses default Pythia8 with the configuration [this configuration](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/share/egconfig/pythia8_hf.cfg).

### pythia8hi

A special, pre-configured case of `<pythia8>` for PbPb collisions (Agantyr model). This uses default Pythia8 with the configuration [this configuration](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/share/egconfig/pythia8_hi.cfg).

### pythia8powheg

This uses default Pythia8 with the configuration [this configuration](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/share/egconfig/pythia8_powheg.cfg).
In addition, that needs a POWHEG output file `powheg.lhe` to be present in the working directory where Pythia8 reads from.

## Box Generators

There are multiple box or gun generators:

* `boxgen`: Generic Box Generator, 10 pions per event by default; this can be customised (see below),
* `fwmugen`: Forward muon generator,
* `hmpidgun`: HMPID pion generator,
* `fwpigen`: Forward pion generator,
* `fwrootino`: Forward rootino generator,
* `zdcgen`: ZDC (A and C side) neutron generator,
* `emcgenele` and `emcgenphoton`: Electron and photon gun for EMC, respectively,
* `fddgen`: FDD (A and C side) muon generator.

### Customising your box generator

For the generic `boxgen` generator, a user can influence the PDG, eta range etc. via `--configKeyValues "BoxGun.<param>=<value>;..."`, see this [header file](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/BoxGunParam.h) for all settings.

Example :
```bash
o2-sim -m PIPE ITS MFT -g boxgen -n 10 --configKeyValues 'BoxGun.pdg=13 ; BoxGun.eta[0]=-3.6 ; BoxGun.eta[1]=-2.45; BoxGun.number=100'
```

This command line will generate 10 events with 100 forward muons, simulating only the beam pipe, the ITS and the MFT.

## Generating from file

Events and their primaries (and secondaries) can also be read from a file and injected into the transport.

### extkinO2

This reads primaries to be transported from an MC kinematics file. Such a file is produced always by a (previous) run of `o2-sim`. Of course the file path to this file has to be passed. A command would look like
```bash
o2-sim -g extkinO2 --extKinFile <path/to/o2sim_Kine.root>
```
Alien paths are compatible as well, provided they follow the syntax `alien:///path/to/file.root`. They will be opened on-the-fly, without the need to download them locally, however you might experience longer simulation times due to the remote source. Alternatively to using the `--extKinFile` flag, the `GeneratorFromO2Kine.fileName` parameter can be used
```bash
o2-sim -g extkinO2 --configKeyValues "GeneratorFromO2Kine.fileName=<path/to/o2sim_Kine.root>"
```
whose value has the priority when both methods are used together.

### evtpool

This generator is a wrapper of extkinO2 but it is optimised for event pools handling.
In particular it offers functionality to

* self-pick a file from a pool
* discover available files in a pool on AliEn or local disk
* makes it easier to generate generic JSON configs &rarr; users don't need to provide a full file path to use (which would be impractical for productions).
An example generation with evtpool is the following:
```bash
o2-sim -g evtpool --configKeyValues "GeneratorEventPool.eventPoolPath=<path/to/evtpools>"
```
where `evtpools`, on AliEn or local disk, can be:
* a folder &rarr; the path is searched for the `evtpool.root` files
* an evtpool.root file

In addition a `.txt` file can be provided on the local disk containing a list of files to be used as event pools.
Event pools files need to be specifically named `evtpool.root` otherwise the simulation will fail (hardcoded setting).

### hepmc

This reads primaries to be transported from a HepMC file. A command would look like
```bash
o2-sim -g hepmc --configKeyValues "HepMC.fileName=<path/to/HepMC/file>"
```
It is important to know which HepMC version is considered: by default `o2-sim` assumes HepMC3, but if this is not the case (as for EPOS4) `HepMC.version=2`
must be added in the configuration keys, otherwise the simulation task could fail.

## Generating using FIFOs 

FIFOs allow not to store data from generators and to feed them directly to o2-sim and they can be used either *manually*, by creating one and then feeding it as HepMC file to both your generator and the o2-sim script, or automatically via `GeneratorHepMC` using the `cmd` parameter.  
The use of the latter, instead of the former, is **highly encouraged** and a few examples are provided in [O2](https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples) inside the `HepMC*` folders.  
This function spawns a simulation task using an external generator provided that this:
- returns HepMC data either to a file or stdout &rarr; this is the only real hard requirement
- accepts a `-s` flag to set the generation seed
- has control of the number of events with a `-n` flag or different mechanism
- has the possibility of setting the impact parameter (`-b` flag).

These flags are automatically fed to the executable (or script) provided with `GeneratorFileOrCmd.cmd=<scriptname>`.  
In most generators these conditions are either available out of the box or they can be satisfied by creating a simple steering script. The only real stopper to run with this method is not having HepMC in the stdout or redirected to a file, however the user must be careful what the other flags do in the provided generator because they could be interpreted in a different way and return unexpected results.  
In order not to provide an impact parameter limit `GeneratorFileOrCmd.bMaxSwitch=none` can be set in the configuration keys, which is useful because your generator might not be able to configure this option by default. An example command to run with automatically generated FIFOs with a generator printing data to stdout is:
```bash
o2-sim -n 100 -g hepmc --seed 12345 --configKeyValues "GeneratorFileOrCmd.cmd=epos.sh -i <optnsFileName>;GeneratorFileOrCmd.bMaxSwitch=none;"
```
where epos.sh is the steering script of EPOS4 which can be found [here](https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples/HepMC_EPOS4). The `-i` flag in the `cmd` parameter is mandatory in order to fetch the .optns file needed for the configuration of the generator: only the filename must be provided and the file (with `.optns` extension) must be available in the current working directory, otherwise the generation will not start. This is because paths are not supported in the original epos executable for the configuration file, however the epos.sh steering script can be preceded by a path (environment variables are allowed). More information are at the user disposal in the README files of each HepMC example folder.  
The generator spawning can be performed also using O2 external generators (discussed in the next paragraph) as done for EPOS4 in this [example](https://github.com/AliceO2Group/O2DPG/tree/master/MC/config/examples/epos4). This feature is very important because it allows us to run the HepMC based generators on hyperloop trains via on-the-fly events generation.  
In case your generator puts data on disk instead you need to specify the fifo filename in which the FIFO will be automatically created via the `GeneratorFileOrCmd.fileNames` parameter. A full example is available through the JETSCAPE generator [here](https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples/HepMC_JETSCAPE).

## External generators

External generators are usually defined in macros that are evaluated at runtime. External generators allow the users
to provide completely custom generator setups and interface other generators than Pythia8 into the simulation. Examples of external generators may be specializations of Pythia8 (via class inheritance), cocktail setups, etc.

Please also refer to the [custom generators page](generatorscustom.md) for a detailed explanation of their implementation.

Such a custom generator is invoked with
```bash
o2-sim -g external --configKeyValues "GeneratorExternal.fileName=<path/to/macro.C>;GeneratorExternal.funcName=<function-signature-to-call(...)>"
```

## Hybrid generator

Most of the generators described until this point of the tutorial can be run simultaneously to create a simulation that will contain multiple sources of events. One of the easiest example is to run Pythia8 while introducing from time to time some events stored in a cache via the extkinO2 generator. Specifically the full list of available generators is:
- pythia8
- pythia8pp
- pythia8hf
- pythia8hi
- pythia8powheg
- boxgen
- hepmc
- evtpool
- extkinO2
- external

The hybrid generator is configured via two parameters:
* configFile &rarr; path to filename of the JSON file used to configure the generators to be included in the hybrid run
* randomize &rarr; if true the execution order of the generators will be randomised (false by default)
* num_workers &rarr; number of threads available when parallel generation mode is enabled

An example JSON configuration file can be found in the hybrid [example folder](https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples/Hybrid) where the script runo2sim.sh can be used as a base to run the generator for the first time, which contains a similar instruction to this one
```
${O2_ROOT}/bin/o2-sim --noGeant -j 4 --run 300000 --configKeyValues "GeneratorHybrid.configFile=/path/to/file.json;GeneratorHybrid.randomize=true" -g hybrid -o genevents --seed 836302859 -n 10
```
A template of the configuration file can be generated via the O2DPG script [${O2DPG_ROOT}/MC/bin/o2_hybrid_gen.py](https://github.com/AliceO2Group/O2DPG/blob/master/MC/bin/o2_hybrid_gen.py) passing as argument to its **gen** flag a list of all the generators you want to use in your simulation. The template generator requires O2 to be loaded in your environment since the needed generators parameter and default values are dynamically taken from the ROOT dictionary, otherwise the script will not work. The newly created file will contain all the parameters needed to be configured (most of them with default values set) and a field called fractions which is an array with all elements set to unity. Each element, in order, corresponds to the number of events to be generated with each generator before passing to the next when running with no randomisation. If no fractions field is present all the elements are assumed to be unity, however if this is set it's important that the size of the array corresponds to the number of generators that will be initialised, otherwise the simulation will not start. These are also used for the randomisation distribution, changing the percentage of usage for each generator when declared. If they are not or each generator has the same fraction the randomisation will be uniform.

For more usage information on both runo2sim.sh and o2_hybrid_gen.py you can always use the \-\-help flag or check the short description at the beginning of their source code.