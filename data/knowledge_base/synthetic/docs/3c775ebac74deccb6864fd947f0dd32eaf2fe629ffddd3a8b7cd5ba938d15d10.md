## Metadata

**Document link:** https://github.com/AliceO2Group/simulation/blob/main/docs/generators/README.md

**Start chunk id:** 3c775ebac74deccb6864fd947f0dd32eaf2fe629ffddd3a8b7cd5ba938d15d10

## Content

---
sort: 1
title: Generators
---

# Generators

This section outlines the documentation and usage of primary generators in O2.

Multiple [generator implementations](https://github.com/AliceO2Group/AliceO2/tree/dev/Generators/include/Generators) are available in O2, including the commonly used [Pythia8](https://pythia.org). These predefined generators can be invoked with the command:
```bash
o2-sim -g <generator-name> [<additionalOptions>]
```

For more detailed information on configurations and testing of generators, refer to [this page](generatorconfig.md).

{% include list.liquid all=true %}