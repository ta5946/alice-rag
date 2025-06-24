---
sort: 5
title: MCStepLogger
---

# MCStepLogger

This page gives an overview of the basic functionality of the MCStepLogger. For a more in-depth description, please refer to [the package's readme](https://github.com/AliceO2Group/VMCStepLogger/tree/master/MCStepLogger).
The MCStepLogger can be used to log and analyse the single steps computed by detector simulation engines built upon the [Virtual Monte Carlo (VMC)](https://vmc-project.github.io/).

When using it with O2 simulations, make sure to use `o2-sim-serial` **instead of** `o2-sim`.

## Basic usage

```bash
LD_PRELOAD=path_to/libMCStepLoggerInterceptSteps.so o2-sim-serial -m PIPE ITS TPC -n 10
```

```bash
[MCLOGGER:] START FLUSHING ----
[STEPLOGGER]: did 28 steps
[STEPLOGGER]: transported 1 different tracks
[STEPLOGGER]: transported 1 different types
[STEPLOGGER]: VolName cave COUNT 23 SECONDARIES 0
[STEPLOGGER]: VolName normalPCB1 COUNT 3 SECONDARIES 0
[STEPLOGGER]: ----- END OF EVENT ------
[FIELDLOGGER]: did 21 steps
[FIELDLOGGER]: VolName cave COUNT 20
[FIELDLOGGER]: ----- END OF EVENT ------
[MCLOGGER:] END FLUSHING ----
```

The stepping logger information can also be directed to an output tree for more detailed investigations. The default output file name is `MCStepLoggerOutput.root` (and can be changed by setting the `MCSTEPLOG_OUTFILE` env variable). To enable this functionality, do

```bash
MCSTEPLOG_TTREE=1 LD_PRELOAD=path_to/libMCStepLogger.so o2-sim-serial ...
```

### Special case on macOS

`LD_PRELOAD` must be replaced by `DYLD_INSERT_LIBRARIES`, e.g. :

```bash
DYLD_INSERT_LIBRARIES=/Users/laurent/alice/sw/osx_x86-64/O2/latest-clion-o2/lib/libMCStepLogger.dylib MCSTEPLOG_TTREE=1 MCSTEPLOG_OUTFILE=toto.root o2-sim-serial -m MCH -g fwmugen -n 1
```

`LD_DEBUG=libs` must be replaced by `DYLD_PRINT_LIBRARIES=1`

`LD_DEBUG=statistics` must be replaced by `DYLD_PRINT_STATISTICS=1`

{% include list.liquid all=true %}
