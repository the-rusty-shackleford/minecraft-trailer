---
title: Trailer — project
type: overview
layer: store
tags: [overview]
---

# Trailer

## What this is

The second vehicle for Vanilla Wheels and the first trailer: a data-only NeoForge 1.21.1
mod (`lowcodefml`) holding a profile with a tongue, cargo, doors and marker lamps, two
Blockbench meshes, a recipe and a lang file, with the protocol nested inside. The body is
nfx's Blockbench project `devtools/art/preview/trailer.bbmodel`; everything shipped is
written from it by `devtools/art/build.py`, his build ported (D-0002).

## Shape

No Java in the mod. `gametest` is a mod of its own: four gametests and a photo booth,
towing behind the Trailblazer taken from Maven Local. The pipeline turns the project half
a turn into the protocol's frame, cuts the +X mesh wheel out and recentres it, wraps cubes
into the profile's folders (lenses, glass, paint) and measures the profile off the cubes.

## How it is verified

`./gradlew check`: four gametests (the profile, towing straight and round a turn, cows
and calves against the room, the chassis recipe) and the booth (the side; hitched behind
the Trailblazer with the doors open and two cows aboard).

## Decisions

D-0001 (superseded): parts named by geometry, not by the generator's header. D-0002:
Trailer 2 is nfx's Blockbench re-creation, under the same ids and recipe.

## Next

1.0.0 (2026-09-09): the generator's bundle. 2.1.0 (2026-09-13): nfx's rebuild -- doors
that swing, rail lamps that follow the car, placed hitched from the hand, solid body, the
lever pose when towed, cargo tilting with the floor -- on Vanilla Wheels 1.5.0 (its
D-0008); past the 2.0.x he shipped to his instance. Watch the first tow on the box with
Rusty: the 2.79-tall box can catch on overhangs (shows as the chain breaking, not lag).


## Release approval - 2026-09-16

Rusty approved the final review, completing their earlier conditional release go.
Version 2.2.0 was published on 2026-09-16 and deployed in pack 1.35.1
after the clean release build and asset verification. The deployed server matched
the published pack and ran at 20 TPS. This supersedes the earlier release holds
and pending presentation/listening review recorded above.
