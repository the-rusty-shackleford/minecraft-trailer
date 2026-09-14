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

The trailer is nfx's Blockbench project, `devtools/art/preview/trailer.bbmodel`, as saved;
`devtools/art/build.py` (his build, ported) turns it into what the protocol reads. The
model is built tongue at -Z and the protocol draws +Z forward, so the whole thing is turned
half a turn about Y, a proper rotation that keeps every face's winding and swaps the face
UVs that must swap. The wheels are meshes, not slab stacks; the +X wheel and hub are cut
out as the wheel mesh, recentred on the tyre, and the profile spins its own at both axle
ends. Cubes are wrapped into the folders the profile names: `lenses`, the thirty amber
rail cubes, drawn full-bright when lit and, with no engine, lit as point marker lamps;
`glass`, the four side windows; `paint`, the light-grey walls, front and roof, near-white
so white dye is the model (the rear doors are not dyeable: door meshes are drawn
untinted). The profile is measured off the cubes: the body's width from the widest wall,
its length coupler to step, four hit boxes tiling the shell, the axle and fenders, and the
tongue -- solid to walkers, since a seatless vehicle's boxes are -- the coupler off the
socket's front face, the rail lamps half a block outside the rails at the front, middle
and rear, the cargo slots on the floor mat, the doors off their folders' pivots with
right-hand angles about +Y (the +X leaf opens with -pi/2; Blockbench's animation
keyframes carry the opposite sign, never copy one in). Units are sixteenths of a block.

## Verifying it

```
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH="$JAVA_HOME/bin:$PATH"
uv run --no-project python devtools/art/build.py     # split the project and write the profile
./gradlew check                                       # gametests and the photo booth (needs a display)
```

Four gametests on a headless server: the profile is a trailer as described; the
Trailblazer (from Maven Local: `./gradlew publishToMavenLocal` in its repo) catches the
tongue, wherever the two profiles put the ball and the coupler, and tows it straight and
round a turn; four cows board and a fifth is refused, a calf at a half; the chassis crafts. The booth photographs the trailer's side and then
hitched behind a Trailblazer with its doors open and two cows aboard; its
`booth: PASS/FAIL` lines are the assertion. Headless: `Xephyr :7 -screen 1280x720 -ac -br
-noreset`, then `DISPLAY=:7 __GLX_VENDOR_LIBRARY_NAME=mesa LIBGL_ALWAYS_SOFTWARE=1
GALLIUM_DRIVER=llvmpipe ./gradlew check`.

## Licence

AGPL-3.0-or-later. Copyright 2026 Rusty Shackleford and nfx.
