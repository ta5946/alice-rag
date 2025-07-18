#!/usr/bin/env bash
#
# This is a simple simulation example showing how to
# start EPOS4 generation automatically using cmd with hepmc output on FIFO
# and simultaneosly use o2-sim for transport

# This script works only with O2sim version starting from the 20/09/2024

# EPOS4 and O2 must be loaded
set -x
if [ ! "${EPOS4_ROOT}" ]; then
    echo "This needs EPOS4 loaded; alienv enter ..."
    exit 1
fi

[ ! "${O2_ROOT}" ] && echo "Error: This needs O2 loaded" && exit 2

cmd="$PWD/epos.sh"
NEV=-1
more=""
optns="example"
eCM=-1
JOBS=2
HEPMC=""
HQ=false

if [ -z "$EPO4VSN" ]; then
    echo "Error: EPOS4 version not found"
    exit 7
fi
if [ "$EPO4VSN" == "4.0.0" ]; then
    HEPMC=";HepMC.version=2"
else
    HEPMC=";HepMC.version=3"
fi

usage()
{
    cat <<EOF
Usage: $0 [OPTIONS]

Options:

  -m,--more    CONFIG      More configurations ($more)
  -n,--nevents EVENTS      Number of events ($nev)
  -i,--input   INPUT       Options file fed to EPOS4 ($optns)
  -j,--jobs    JOBS        Number of jobs ($JOBS)
  -e,--ecm     ENERGY      Center-of-Mass energy
  -h,--help                Print these instructions
  -hq          HQ          Enable EPOS4HQ
  --                       Rest of command line sent to o2-sim

COMMAND must be quoted if it contains spaces or other special
characters

Below follows the help output of o2-sim-dpl-eventgen

EOF
}

if [ "$#" -lt 2 ]; then
    echo "Running with default values"
fi

while test $# -gt 0 ; do
    case $1 in
        -m|--more)    more="$2" ; shift ;;
        -n|--nevents) NEV=$2 ; shift ;;
        -i|--input)   optns=$2 ; shift ;;
        -j|--jobs)    JOBS=$2 ; shift ;;
        -e|--ecm)     eCM=$2 ; shift ;;
        -hq)          HQ=true ; shift ;;
        -h|--help) usage; o2-sim-dpl-eventgen --help full ; exit 0 ;;
        --)           shift ; break ;;
        *) echo "Unknown option '$1', did you forget '--'?" >/dev/stderr
           exit 3
           ;;
    esac
    shift
done

echo "Options file: $optns"

if [ ! -f $optns.optns ]; then
    echo "Error: Options file $optns.optns not found"
    exit 4
fi

# Set number of events in optns file
if [ ! $NEV -eq -1 ]; then
    echo "Setting number of events to $NEV"
    if grep -Fq "nfull" $optns.optns; then
        sed -i "/nfull/c\set nfull $NEV" $optns.optns
    else
        echo "set nfull $NEV" >> $optns.optns
    fi
else
    echo "Number of events not set, checking optns file..."
    if grep -Fq "nfull" $optns.optns; then
        NEV=$(grep -F "nfull" $optns.optns | awk '{print $3}')
        echo "Number of events set to $NEV"
    else
        echo "Error: Number of events not set in EPOS4"
        exit 5
    fi
fi

# Set ECM

if [ ! $eCM -eq -1 ]; then
    echo "Setting eCM to $eCM"
    if grep -Fq "ecms" $optns.optns; then
        sed -i "/ecms/c\set ecms $eCM" $optns.optns
    else
        echo "set ecms $eCM" >> $optns.optns
    fi
else
    echo "Energy not set, checking optns file..."
    if grep -Fq "ecms" $optns.optns; then
        eCM=$(grep -F "ecms" $optns.optns | awk '{print $3}')
        echo "Energy set to $eCM"
    else
        echo "Error: eCM not set in EPOS4"
        exit 6
    fi
fi

# Set HQ mode

if [ "$HQ" = true ]; then
    echo "Setting HQ mode"
    if grep -Fq "ihq" $optns.optns; then
        sed -i "/ihq/c\set ihq 1" $optns.optns
    else
        echo "set ihq 1" >> $optns.optns
    fi
    if [ -z "$EPO4HQVSN" ]; then
        echo "Error: EPOS4HQ version not found"
        exit 7
    else
        HEPMC=";HepMC.version=3"
    fi
else
    echo "Turning OFF HQ mode"
    if grep -Fq "ihq" $optns.optns; then
        sed -i "/ihq/c\set ihq 0" $optns.optns
    else
        echo "set ihq 0" >> $optns.optns
    fi
fi

# Starting simulation => seed is fed automatically to epos with the --seed flag. HepMC.version = 2 is mandatory for version 4.0.0
# otherwise the simulation won't work.
# Seed is automatically set to Random by the epos.sh script because the --seed option with o2-sim-dpl-eventgen does not feed the number to GeneratorHepMC
o2-sim-dpl-eventgen -b --nEvents ${NEV} --generator hepmc --configKeyValues "GeneratorFileOrCmd.cmd=$cmd -i $optns;GeneratorFileOrCmd.bMaxSwitch=none$HEPMC;${more}" |\
                    o2-sim-mctracks-to-aod -b | o2-analysis-mctracks-to-aod-simple-task -b
