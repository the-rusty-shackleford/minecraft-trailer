---
title: Trailer — project
type: overview
layer: store
tags: [overview]
---

# Trailer

## What this is

The second vehicle for Vanilla Wheels and the first trailer: a data-only NeoForge 1.21.1
mod (`lowcodefml`) holding a profile with a tongue, cargo and doors, two OBJ meshes, a
texture, a recipe and a lang file, with the protocol nested inside. The generator's
bundle is committed under `devtools/art/src/`; everything shipped is written by
`devtools/art/build.py`.

## Shape

No Java in the mod. `gametest` is a mod of its own: four gametests and a photo booth,
towing behind the Trailblazer taken from Maven Local. The pipeline names parts by
geometry, turns and drops the mesh, cuts out and turns the wheel, makes the atlas, and
writes the profile.

## How it is verified

`./gradlew check`: four gametests (the profile, towing straight and round a turn, cows
and calves against the room, the chassis recipe) and the booth (the side; hitched behind
the Trailblazer with the doors open and two cows aboard).

## Decisions

D-0001: parts are named by geometry, not by the bundle's header; the wheel is turned to
put its axle across the vehicle.

## Next

1.0.0 (2026-09-09). Watch the door swing and the cows' slots with Rusty.
