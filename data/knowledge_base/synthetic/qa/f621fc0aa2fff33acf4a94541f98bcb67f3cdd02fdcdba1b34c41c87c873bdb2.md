## Metadata

**Document link:** https://github.com/AliceO2Group/O2DPG/blob/master/DATA/production/configurations/2021/ctf_recreation/setenv_extra_ctf_recreation_muon.sh

**Start chunk id:** f621fc0aa2fff33acf4a94541f98bcb67f3cdd02fdcdba1b34c41c87c873bdb2

## Content

**Question:** What is the difference between the `WORKFLOW_DETECTORS_CTF` and `WORKFLOW_DETECTORS` environment variables, and how do they relate to the ALICE O2 simulation documentation?

**Answer:** The `WORKFLOW_DETECTORS_CTF` and `WORKFLOW_DETECTORS` environment variables are both used in the ALICE O2 simulation documentation to specify the detectors involved in the workflow. 

`WORKFLOW_DETECTORS_CTF` specifically includes the CTF detector, alongside ITS, MFT, MCH, and MID. This variable likely refers to a scenario where the CTF data processing is required or included in the simulation workflow.

`WORKFLOW_DETECTORS`, on the other hand, does not include CTF and only lists ITS, MFT, MCH, and MID. This variable would be used when the CTF detector is not part of the simulation or data processing.

Both variables serve to configure the simulation to include or exclude the CTF detector, ensuring that only the necessary detector data is processed according to the specific requirements of the simulation or workflow.