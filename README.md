# Trailer

A livestock trailer for [Vanilla Wheels](https://github.com/the-rusty-shackleford/minecraft-vanilla-wheels)
on NeoForge 1.21.1. Hitches behind any vehicle with a rear hitch -- the
[Trailblazer](https://github.com/the-rusty-shackleford/minecraft-trailblazer) has one -- and
follows the way a real trailer does, its axle dragged along the line to the hitch, posed
as a lever on its axle with the coupler on the car's ball. Room for four grown animals or
eight young, or two and four, behind double rear doors that swing open; side windows to
see them through; amber marker lamps along the rails that follow the towing car's
headlights. There is no Java in it: the trailer is a vehicle profile and two Blockbench
meshes, and the protocol does the rest, so towing, doors and loading are documented there.
Trailer 2 is nfx's Blockbench re-creation of the first trailer -- the same footprint, axle,
coupler and hinges to within a tenth of a block -- under the same ids and recipe, so
trailers already in a world and chassis already crafted simply wear the new body.

## Getting one

- **Chassis**: six steel blocks over three iron bars, in a `B I B / B B B / I I I` grid.
- **Build**: the chassis and two wheels in a Mechanic Lift, and Build. No engine. Paint it
  there with a dye; it is white to begin with.
- **Pick up**: crouch and right-click with the wrench.

## Using it

Hold the trailer and right-click a vehicle with a rear hitch: it is put down coupler on the
ball, hitched. Or back a vehicle's rear hitch to within half a block of the tongue while
moving and it catches; crouch and right-click the tongue to let go. Crouch and right-click
a rear door, empty-handed, to open or shut both; right-click the trailer with a lead and
every animal on your leads within ten blocks boards while there is room (an adult a whole
share, a young one a half); crouch and right-click the trailer holding a lead with the
doors open and animals aboard to let them out behind. Animals never board through shut
doors, and nobody walks through the body. The rail lamps come on with the car's headlights (H).

Numbers: mass 1.2, two wheels of 0.4 blocks, the coupler 2.58 blocks ahead of the centre,
the body 2.35 blocks wide, 5.18 long coupler to step and 2.79 high; climbs one block.

## How it is made

`devtools/art/preview/trailer.bbmodel` is an approved cosmetic derivative of nfx's
Blockbench project. The original is preserved in `devtools/art/reference/`, with its
attribution and checksums. A chamfered roof cap, continuous fender crowns, recessed hubs, corner and window trim, lower panel beads, and quieter metal and rubber shades.

Edit the Blockbench source, then run `devtools/art/build.py --appearance-only`.
It exports only the body and wheel meshes, supports cube and polygon faces, and refuses
to run if the vehicle profile differs from the frozen released contract. It does not
derive gameplay from the reshaped art or rewrite the profile, recipes or language files.
The importer retains the proper half-turn from the source’s tongue-at-minus-Z orientation into the protocol’s plus-Z frame, wheel centring, and glass, lamp and paint selections. The rear doors retain their original hinges and finish.

See D-0003 for the art direction and gameplay boundary. The cosmetic changes in 2.3.0 do not change the driving, interactions or construction described above.

## Verifying it

```
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH="$JAVA_HOME/bin:$PATH"
uv run --no-project python devtools/art/build.py --appearance-only
uv run --no-project --with pillow python -m unittest discover -s devtools/art -p "test_appearance.py"
./gradlew check                                       # gametests and the photo booth (needs a display)
```

Five gametests on a headless server: the profile is a trailer as described; the
Trailblazer (from Maven Local: `./gradlew publishToMavenLocal` in its repo) catches the
tongue, wherever the two profiles put the ball and the coupler, and tows it straight and
round a turn; four cows board and a fifth is refused, a calf at a half; crouch-clicking either door works across its leaf while the roof does
not toggle it; the chassis crafts. The booth photographs the trailer's side and then
hitched behind a Trailblazer with its doors open and two cows aboard; its
`booth: PASS/FAIL` lines are the assertion. For server-only checks, run
`./gradlew --no-watch-fs check -PskipBooth`. For the shader booth, use a native GPU display
with Iris, Sodium and Complementary in `run/booth/`. Verify host clients and Xephyr first,
reuse the existing display, and run only one rendering client. The booth mutes itself and exits.

The cosmetic booth also checks dye against the stock wall finish, captures the coupler joint, and logs five-second fixed-view frame samples (`booth-performance`). Shader colour checks use separate body and marker regions with negative controls. The towing fixture uses the current local Trailblazer 1.7.0 artifact.

## Release 2.3.0

The approved cosmetic derivative ships with Vanilla Wheels 1.7.0 and Luminance 1.1.0. Vehicle gameplay data and original supplied-model references are preserved. Update every client and the server together for network protocol 4.

## Licence

AGPL-3.0-or-later. Copyright 2026 Rusty Shackleford and nfx.

## Shared materials dependency

Version 2.3.1 bundles Vanilla Wheels 1.7.2, which requires Metals and Materials
as a separately installed mod on both client and server. Mod Hub includes it
in our pack. Vehicle profiles, models, recipes and handling are unchanged.
