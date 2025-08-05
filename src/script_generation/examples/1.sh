#!/usr/bin/env bash

# Required variables
export ALIEN_JDL_LPMRUNNUMBER=545312
export ALIEN_JDL_LPMANCHORPASSNAME=apass4
export ALIEN_JDL_LPMINTERACTIONTYPE=Pb-Pb
export SPLITID=25
export NTIMEFRAMES=3

# Optional variables
export ALIEN_JDL_CPULIMIT=12
export ALIEN_JDL_SIMENGINE=TGeant4
export ALIEN_JDL_ANCHOR_SIM_OPTIONS="-gen pythia8 --trigger-external"
export NSIGEVENTS=8000
export CYCLE=1

# Start the workflow (will run)
${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
