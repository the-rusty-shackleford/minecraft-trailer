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
an approved derivative of nfx's Blockbench project `devtools/art/preview/trailer.bbmodel`; the meshes are
exported from it by `devtools/art/build.py`, his build ported (D-0003).

## Shape

No Java in the shipped mod. The separate gametest source set contains the real-server
checks and client booth. `build.py --appearance-only` splits the Blockbench source,
preserves selector/animation structure and uses the frozen released gameplay profile.
It does not write gameplay or language data. Original source and profile references,
with attribution, are kept under `devtools/art/reference/` (D-0003).

## How it is verified

`./gradlew check`: five gametests (the profile, towing straight and round a turn, cows
and calves against the room, door hit regions, the chassis recipe) and the booth (the side; hitched behind
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

## Cosmetic work — held, 2026-09-17

D-0003 records Rusty's approved art direction and intentionally edited derivative.
A chamfered roof cap, continuous fender crowns, recessed hubs, corner and window trim, lower panel beads, and quieter metal and rubber shades. Gameplay remains frozen to v2.2.0. New releases remain HELD.
Independent driver/observer multiplayer checks, the historical movement-warning route,
and representative 4–8-player capacity, distant tracking and DH load remain open;
local booths and isolated frame timings do not close them.

The cosmetic booth also checks dye against the stock wall finish, captures the coupler joint, and logs five-second fixed-view frame samples (`booth-performance`). Shader colour checks use separate body and marker regions with negative controls. The towing fixture uses the current local Trailblazer 1.6.0 artifact.

## Release authorization — 2026-09-17

Rusty approved the final vehicle cosmetics, then explicitly requested the release.
Version 2.3.0 is the coordinated release version, superseding the prior hold.
The release set is Luminance 1.1.0, Vanilla Wheels 1.7.0 (network protocol 4),
Trailblazer 1.7.0, Farmer's Pickup 1.3.0 and Trailer 2.3.0, targeting pack 1.36.0.
All peers must update together. Vehicle artwork changes leave the existing gameplay
profiles, recipes, seats and interaction anchors unchanged; the separately approved
collision and moving-light changes ship in the shared libraries.

Independent driver/observer multiplayer, the historical live movement-warning route,
and representative 4–8-player tracking/DH capacity remain open follow-ups. Local tests
do not establish those results. Release authorization does not claim those checks passed.

## Published release — 2026-09-17

[Version 2.3.0](https://github.com/the-rusty-shackleford/minecraft-trailer/releases/tag/v2.3.0) is published and deployed in pack 1.36.0.
The coordinated set passed 96 JUnit tests, 59 real-server GameTests and all five
Iris/Complementary booths on clean release builds. Downloaded release assets match
the validated jars; nested dependencies are the exact newly built artifacts.
The three cosmetic vehicle profiles remain identical to their preserved references.

Both pack archives were verified against the source. Deployment occurred with zero
players online; installed server hashes match, and Mod Hub reports pack parity.
The initial empty-server sample was 20 TPS. Startup retained the same 36 pre-existing
third-party error messages, with none added. This does not close the multiplayer,
historical movement-warning or representative capacity follow-ups above.

## Shared materials dependency — 2026-09-18, unreleased

Version 2.3.1 rebuilds with Vanilla Wheels 1.7.2 to remove the indirectly bundled
Metals and Materials jar, following Vanilla Wheels D-0013 and Rusty's "Proceed."
Metals and Materials is installed separately on both sides. Models, recipes and
profiles are unchanged. Unit/server checks, recursive jar/payload audits and complete-pack startup passed; release is held.

Validation: see Metals and Materials `devtools/verification/separate-dependency.md`;
all six packaging builds and the complete-pack client/server check passed.
