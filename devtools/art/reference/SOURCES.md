# Cosmetic reference inputs

The original source is nfx's Blockbench project from `v2.2.0`, preserved byte for byte.
Copyright 2026 Rusty Shackleford and nfx; AGPL-3.0-or-later.

- `trailer-before-cosmetics.bbmodel` SHA-256: `0067f5159ebd708673bc68071c674c89ee8dc02b9030821aae77494601ac0221`
- `released-profile.json` SHA-256: `9b3638c089814f6c298744a5ee06caaa8f7b506e9f6672bdcd27d1a4be3dd895`

`../preview/trailer.bbmodel` is the intentional cosmetic derivative approved by Rusty
on 2026-09-16. It is not a verbatim collaborator delivery. See D-0003.
Automobility 0.5.0.h's steel motorcar supplied a finish reference; none of its geometry
or textures are included in this derivative.

The profile is a frozen comparison input. The importer checks it before exporting
meshes and never rewrites gameplay data. Review a future gameplay change separately;
do not regenerate or refresh this reference merely to bypass that guard.
