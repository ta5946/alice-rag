---
sort: 0
title: Getting started
---

# Getting started

The purpose of the `o2-sim` executable is to simulate the passage of particles emerging from a collision inside the detector and to obtain their effect in terms of energy deposits (called hits) which could be converted into detectable signals. It is the driver executable which will spawn a topology of sub-processes that interact via messages in a distributed system.

## Usage overview

There are 2 executables used to steer a simulation run
1. `o2-sim`: Runs the simulation using multiple worker processes. Also the particle generation runs in a dedicated process as well as the task responsible for collecting all detector hits created in respective simulation processes. This is also used as the default for all examples described in this documentation.
1. `o2-sim-serial`: This only launches one single simulation process. Needs to be used in some special simulations and it will be mentioned explicitly when `o2-sim` cannot be used.

### Quick start example

A typical (exemplary) invocation is of the form

```bash
o2-sim -n 10 -g pythia8pp -e TGeant4 -j 2 --skipModules ZDC,PHS
```
which would launch a simulation for 10 pythia8 events on the whole ALICE detector but ZDC and PHOS, using Geant4 on 2 parallel worker processes. There is a variety of command-line arguments to configure the simulation. For a detailed list, please refer to the [transport section](../transport/).

### Alien GRID token

Running the simulation requires a valid alien token. If you do not yet have a certificate, please follow these [instructions](https://alice-doc.github.io/alice-analysis-tutorial/start/cert.html) and [this](https://alice-doc.github.io/alice-analysis-tutorial/start/cert.html#convert-your-certificate-for-using-the-grid-tools) in particular.

To obtain a token, run
```bash
alien-token-init
```
after loading your `alienv` environment.
