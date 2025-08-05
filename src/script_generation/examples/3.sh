#!/usr/bin/env bash

# Invalid ALIEN_JDL_LPMINTERACTIONTYPE and SPLITID:
export ALIEN_JDL_LPMRUNNUMBER=546789
export ALIEN_JDL_LPMANCHORPASSNAME=apass4
export ALIEN_JDL_LPMINTERACTIONTYPE=Au-Au
export SPLITID=150
export NTIMEFRAMES=5

# Invalid ALIEN_JDL_SIMENGINE and CYCLE
export ALIEN_JDL_CPULIMIT=10
export ALIEN_JDL_SIMENGINE=Geant5
export NSIGEVENTS=12000
export CYCLE=-2

# Start the workflow (will fail due to invalid variables)
${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
