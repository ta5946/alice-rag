---
sort: 2
title: MC kinematics
---

# MC kinematics

The MC kinematics is always produced when `o2-sim` is run. It contains the initial kinematic information of primaries (as produced by the [generator](../generators/)) and secondaries (as produced during the transport) at their production vertex. That also includes particles which are not actually transported.
This could be intermediate particles from the generator such as quarks and gluons or very short-lived particles during transport.

It can be extremely informative and useful to take a look at what is inside, in particular if there are problems with the simulation chain which might be seen at a later stage (e.g. analysis) such as
* a certain expected particle is missing,
* some specific tracks have odd kinematics,
* expected energy deposits are off or missing,
* etc.
In fact, before running a full simulation or even a large-scale production, it should be made sure, that what is expected at the very early stage of simulation is sane.

## How to browse the kinematics file

Usually, the file is called `<prefix>_Kine.root` and it contains a tree `o2sim`. The branch that is typically most important to look at is `MCTracks` which stores - per event - `std::vector<o2::MCTrack>`. The first part of an example macro might look like
```cpp
int analyseKine(const char* path)
{
    TFile inputKine(path, "READ");
    auto tree = (TTree*)inputKine.Get("o2sim");
    std::vector<o2::MCTrack>* tracks{};
    tree->SetBranchAddress("MCTrack", &tracks);
    for (int ev = 0; ev < tree->GetEntries(); ++ev) {
        tree->GetEntry(ev);
        for (auto& track : *tracks) {
            // do something for each track
        }
    }

    return 0;
}
```

A 2nd, suggested, method is to use the MCKinematicsReader class:
```c++
// init the reader from the transport kinematics file (assuming here prefix o2sim)
o2::steer::MCKinematicsReader reader("o2sim", o2::steer::MCKinematicsReader::Mode::kMCKine);

// loop over all events in the file
for (int event = 0; event < reader.getNEvents(0); ++event) {
  // get all Monte Carlo tracks for this event; not that this is the short version of
  // std::vector<MCTrack> const& tracks = reader.getTracks(source, event);
  std::vector<MCTrack> const& tracks = reader.getTracks(event);

  // analyse tracks
}
```
Next to reading pure kinematic files, the MCKinematicsReader also offers functionality to retrieve tracks for a given MC label.

In the loop over the tracks all kinds of things might be done:
* check PDG properties,
* check kinematics or production vertex,
* check child-parent relations among particles,
* etc.
There are various different methods to access the properties of an `o2::MCTrack` object as can be seen in the [source code](https://github.com/AliceO2Group/AliceO2/blob/dev/DataFormats/simulation/include/SimulationDataFormat/MCTrack.h).

A useful utility is the `o2::mcutils::MCTrackNavigator` class which consists mostly of static functions which can be used for browsing through the tracks, in particular to resolve child-parent relations. For instance, one can find the child tracks
```cpp
// inside the track loop
auto child0 = o2::mcutils::MCTrackNavigator::getDaughter0(track, *tracks);
auto child1 = o2::mcutils::MCTrackNavigator::getDaughter1(track, *tracks);
```
There are a lot more useful methods as you can see in the [source code](https://github.com/AliceO2Group/AliceO2/blob/dev/DataFormats/simulation/include/SimulationDataFormat/MCUtils.h).

## More specific examples

Here are some small snippets with some more specific examples

### Check whether track left hits

This snippet shows how to check whether a track left at least one hits somewhere and also, whether it left a hit in the FV0 detector.
```c++
// init the reader from the transport kinematics file (assuming here prefix o2sim)
o2::steer::MCKinematicsReader reader("o2sim", o2::steer::MCKinematicsReader::Mode::kMCKine);

// this is assuming a simple signal MC, aka only one generator and no embedding
int source = 0;

// loop over all events in the file
for (int event = 0; event < reader.getNEvents(0); ++event) {
  // get all Monte Carlo tracks for this event; not that this is the short version of
  // std::vector<MCTrack> const& tracks = reader.getTracks(source, event);
  std::vector<MCTrack> const& tracks = reader.getTracks(event);
  o2::dataformats::MCEventHeader const& header = reader.getMCEventHeader(source, event);
  // now we need to know how our detector mask looks like for this event
  std::vector<int> const& detId2HitBitLUT = header.getDetId2HitBitLUT();
  // analyse tracks
  for (auto& track : *tracks) {
    if (track.hasHits()) {
      // do something if there is at least a hit somewhere
    }
    if (track.leftTrace(o2::detectors::DetID::FV0, detId2HitBitLUT)) {
      // do something if there is a FV0 hit
    }
    // anything else
  }
}
```

## Simulate according to the MC kinematics

If you want to inject the exact same primaries from a previous simulation, please have a look at the [generator section](../generators/generatorso2.md#extkino2).
