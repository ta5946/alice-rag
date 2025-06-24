---
sort: 3
title: Implement your own generator
---

# Implement your own generator

Users can implement their own custom primary generator. To integrate it into an O2 simulation, it must at least derive from [`FairGenerator`](https://github.com/FairRootGroup/FairRoot/blob/master/fairroot/base/sim/FairGenerator.h). However, the easiest to use O2-specific class and derive from [`Generator`](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/Generator.h) or even
from [`GeneratorTGenerator`](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/GeneratorTGenerator.h) and the usage of the latter two is recommended. It might be instructive to browse the [O2DPG repository](https://github.com/AliceO2Group/O2DPG) for some inspiration, checkout for instance
[this one](https://github.com/AliceO2Group/O2DPG/blob/master/MC/config/PWGDQ/external/generator/GeneratorCocktailPromptCharmoniaToMuonEvtGen_pp13TeV.C).

## Generator and GeneratorTGenerator

The central step to make sure that created particles will find their way to the particle stack, the corresponding `TParticle` objects need to be added to the `Generator::mParticles` member which is simply a `std::vector`. In case you explicitly add particles to that member or if you override `Generator::importParticles()`, you need to make sure that the particles' status codes and tracking flags
are set correctly (see [here](README.md#generator-status-codes-flagging-particles-to-be-trackedtransported)).
Hence, making sure that a particle will/won't be tracked and that it always has a correctly encoded status code is the responsibility of the user responsible for the custom generator implementation.

If you derive from `GeneratorTGenerator` and neither override `Generator::importParticles` nor change `Generator::mParticles` yourself, note that all particles will be checked automatically for a correct status encoding. If it is found to be not encoded, the `TParticle`'s status code is **assumed to be the HepMC code**.
In addition, only particles with a HepMC status of 1 will be tracked (that was the default behaviour of Run2 simulations).

## Tweak existing generators

Of course, one can also derive from an already fully-functional generator implementations, for instance from [`GeneratorPythia8`](https://github.com/AliceO2Group/AliceO2/blob/dev/Generators/include/Generators/GeneratorPythia8.h) as it is done [here](https://github.com/AliceO2Group/O2DPG/blob/master/MC/config/PWGLF/pythia8/generator_pythia8_longlived.C).


## Troubleshooting

Here are a few more hints and the solution to common issues you might face

### ROOTCLING/CLING-related problems

When you include headers in the macro, the following or similar errors and warnings might occur during runtime:
```bash
<path/to/your/software>/O2/o2-latest/include/DetectorsCommonDataFormats/UpgradesStatus.h:16:9: warning: 'ENABLE_UPGRADES' macro redefined [-Wmacro-redefined]
#define ENABLE_UPGRADES
        ^
...
<path/to/your/software>/FairLogger/v1.11.1-2/include/fairlogger/Logger.h:435:48: note: expanded from macro 'FAIR_LOGF'
#define FAIR_LOGF(severity, ...) LOG(severity) << fmt::sprintf(__VA_ARGS__)
...
```
The problem here is that `ROOT` can find already quite few header files (as well as libraries) and dictionaries and therefore has knowledge about definitions and symbols therein. To solve this problem, an include guard has to be added to the top of the macro like so
```c++
#if !defined(__CLING__) || defined(__ROOTCLING__)

# ..the headers go here.

#endif
```
Note that this is true for `O2`-related headers as well as `FairRoot` and all other software packages that make their classes and functions known via `ROOT` dictionaries and are added to `ROOT_INCLUDE_PATH`. For other headers and libraries that do not have dictionaries, you might need the includes and also load the libraries.
You can have a look [here](https://github.com/njacazio/O2DPG/blob/8b6feb295867394663c2a1b01a736cfaed8449c1/MC/config/PWGDQ/EvtGen/GeneratorEvtGen.C) for an example of how the `EvtGen` package/library comes in.
