#!/usr/bin/env bash

# Missing ALIEN_JDL_LPMRUNNUMBER and ALIEN_JDL_LPMINTERACTIONTYPE
export ALIEN_JDL_LPMANCHORPASSNAME=apass3
export SPLITID=15
export NTIMEFRAMES=2

# Optional variables
export ALIEN_JDL_CPULIMIT=6
export ALIEN_JDL_SIMENGINE=TGeant3
export NSIGEVENTS=5000

# Start the workflow (will fail due to missing required variables)
${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
