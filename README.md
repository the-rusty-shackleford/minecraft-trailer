# Trailer

A livestock trailer for [Vanilla Wheels](https://github.com/the-rusty-shackleford/minecraft-vanilla-wheels)
on NeoForge 1.21.1. Hitches behind any vehicle with a rear hitch -- the
[Trailblazer](https://github.com/the-rusty-shackleford/minecraft-trailblazer) has one -- and
follows the way a real trailer does, its axle dragged along the line to the hitch. Room
for four grown animals or eight young, or two and four, behind double rear doors; side
windows to see them through. There is no Java in it: the trailer is a vehicle profile,
two meshes and a texture, and the protocol does the rest, so towing, doors and loading
are documented there.

## Getting one

- **Chassis**: six steel blocks over three iron bars, in a `B I B / B B B / I I I` grid.
- **Build**: the chassis and two wheels in a Mechanic Lift, and Build. No engine. Paint it
  there with a dye; it is white to begin with.
- **Pick up**: crouch and right-click with the wrench.

## Using it

Back a vehicle's rear hitch to within half a block of the tongue while moving and it
catches; crouch and right-click the tongue to let go. Crouch and right-click a rear door
to open both; right-click the trailer with a lead and every animal on your leads within
ten blocks boards while there is room (an adult a whole share, a young one a half);
crouch and right-click an open door with animals aboard to let them out behind; empty and
open, the same click shuts the doors. Animals never board through shut doors.

Numbers: mass 1.2, two wheels of 0.4 blocks, the tongue 2.6 blocks ahead of the centre,
the body 2.3 blocks wide and 2.1 high.

## How it is made

`devtools/art/build.py` turns the generator's bundle (committed under `devtools/art/src/`)
into what the protocol reads. The bundle's group names are declared in a header and never
attached to faces, so the four parts the protocol selects -- the two wheels with their
hubs and the two rear doors -- are named again by their geometry. The mesh is turned half
a turn so the front is +Z and dropped so the tyres meet the ground; the left wheel and hub
are cut out into the wheel mesh, turned a quarter turn so the axle runs across the vehicle
(the bundle's tyres faced forward), and every wheel leaves the frame. There is no texture
in the bundle: an atlas of swatches is made from the material colours, the body ones in
grey so a dye colours them, the glass with alpha, and every face is given coordinates
inside its swatch. Units are blocks, so the profile's scale is 1.

## Verifying it

```
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH="$JAVA_HOME/bin:$PATH"
uv run --no-project python devtools/art/build.py     # regenerate the meshes, texture, profile
./gradlew check                                       # gametests and the photo booth (needs a display)
```

Four gametests on a headless server: the profile is a trailer as described; the
Trailblazer (from Maven Local: `./gradlew publishToMavenLocal` in its repo) catches the
tongue and tows it straight and round a turn; four cows board and a fifth is refused, a
calf at a half; the chassis crafts. The booth photographs the trailer's side and then
hitched behind a Trailblazer with its doors open and two cows aboard; its
`booth: PASS/FAIL` lines are the assertion. Headless: `Xephyr :7 -screen 1280x720 -ac -br
-noreset`, then `DISPLAY=:7 __GLX_VENDOR_LIBRARY_NAME=mesa LIBGL_ALWAYS_SOFTWARE=1
GALLIUM_DRIVER=llvmpipe ./gradlew check`.

## Licence

AGPL-3.0-or-later. Copyright 2026 Rusty Shackleford and nfx.
