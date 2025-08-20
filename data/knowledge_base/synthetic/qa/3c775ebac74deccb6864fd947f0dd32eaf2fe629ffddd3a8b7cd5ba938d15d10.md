## Metadata

**Document link:** https://github.com/AliceO2Group/simulation/blob/main/docs/generators/README.md

**Start chunk id:** 3c775ebac74deccb6864fd947f0dd32eaf2fe629ffddd3a8b7cd5ba938d15d10

## Content

**Question:** What are the steps to invoke a generator other than Pythia8 using the `o2-sim` command, and what additional information can be found for configuring and testing these generators?

**Answer:** To invoke a generator other than Pythia8 using the `o2-sim` command, you would use the following syntax:

```bash
o2-sim -g <generator-name> [<potentialOtherArgs>]
```

Replace `<generator-name>` with the name of the generator you wish to use, and optionally add `<potentialOtherArgs>` for any additional arguments required by the specific generator.

For more detailed information on configuring and testing these generators, refer to the documentation file `generatorconfig.md`.