"""The Trailer as a Blockbench project, for editing by hand.

Run from the repository root:

    uv run --no-project python devtools/art/to_bbmodel.py

Reads the generator's OBJ and MTL from devtools/art/src/ and writes
devtools/art/preview/trailer.bbmodel: a free-format project in which each of
the bundle's 82 axis-aligned boxes is a named cube and each of its four round
parts (two tyres, two hubs) is a named mesh element, textured with a swatch
atlas of the MTL colours.

The conversion is exact: the OBJ's parts are found as connected sets of faces
(the bundle never shares a vertex between parts), a set that is six quads on
eight vertices with every quad flat on an axis is a cube, and anything else is
kept as a mesh. The 86 group names in the OBJ header are attached to faces
nowhere, but they are declared in the order the parts are emitted, which is
how each part gets its name; the script checks that the four names for the
round parts land on the four non-cube parts and refuses to write otherwise.

Coordinates: the bundle's blocks become Blockbench units (x16), the bundle's
front stays at -Z (north, the same way the Trailblazer's project faces), and
the whole thing is dropped so the tyres touch y = 0. The bundle's tyres face
forward, as build.py notes; each wheel and its hub are turned a quarter about
Y around the wheel's centre so the axle runs across the trailer.
"""

from __future__ import annotations

import base64
import json
import sys
import tempfile
import uuid
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import write_png  # noqa: E402  (the same PNG writer build.py uses)

SRC = Path(__file__).resolve().parent / "src"
OUT = Path(__file__).resolve().parent / "preview" / "trailer.bbmodel"
OBJ = SRC / "trailblazer_animal_trailer.obj"
MTL = SRC / "trailblazer_animal_trailer.mtl"
SCALE = 16.0
SWATCH = 8  # texture pixels per material swatch
NS = uuid.UUID("7b1f6a7e-2f6a-4c0e-9d0e-7a11e7000000")
EPS = 1e-6


def uid(*parts: object) -> str:
    return str(uuid.uuid5(NS, "/".join(map(str, parts))))


# ------------------------------------------------------------------ reading


def read_mtl(path: Path) -> dict[str, tuple[int, int, int, int]]:
    colours: dict[str, tuple[int, int, int, int]] = {}
    name = None
    for line in path.read_text().splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "newmtl":
            name = p[1]
            colours[name] = (255, 255, 255, 255)
        elif p[0] == "Kd" and name:
            r, g, b = (round(float(x) * 255) for x in p[1:4])
            colours[name] = (r, g, b, colours[name][3])
        elif p[0] == "d" and name:
            colours[name] = colours[name][:3] + (round(float(p[1]) * 255),)
    return colours


def read_obj(path: Path):
    """Vertices, faces as (vertex-index list, material), and header group names in order."""
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[list[int], str]] = []
    groups: list[str] = []
    mat = "default"
    for line in path.read_text().splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "v":
            verts.append(tuple(float(x) for x in p[1:4]))
        elif p[0] == "g":
            groups.append(p[1])
        elif p[0] == "usemtl":
            mat = p[1]
        elif p[0] == "f":
            faces.append(([int(t.split("/")[0]) - 1 for t in p[1:]], mat))
    return verts, faces, groups


# ---------------------------------------------------------------- splitting


def parts(faces) -> list[list[int]]:
    """Face indices grouped by shared vertices, ordered by first face."""
    owner: dict[int, int] = {}  # vertex -> part id
    members: dict[int, list[int]] = defaultdict(list)
    next_id = 0
    for fi, (vs, _) in enumerate(faces):
        ids = {owner[v] for v in vs if v in owner}
        if not ids:
            pid = next_id
            next_id += 1
        else:
            pid = min(ids)
            for other in ids - {pid}:  # merge
                for v in list(owner):
                    if owner[v] == other:
                        owner[v] = pid
                members[pid].extend(members.pop(other))
        for v in vs:
            owner[v] = pid
        members[pid].append(fi)
    return [sorted(members[k]) for k in sorted(members, key=lambda k: min(members[k]))]


def as_cube(verts, faces, part: list[int]):
    """(lo, hi, {face-direction: material}) if the part is an axis-aligned box, else None."""
    if len(part) != 6:
        return None
    vs = {v for fi in part for v in faces[fi][0]}
    if len(vs) != 8:
        return None
    pts = [verts[v] for v in vs]
    lo = tuple(min(p[a] for p in pts) for a in range(3))
    hi = tuple(max(p[a] for p in pts) for a in range(3))
    mats: dict[str, str] = {}
    for fi in part:
        fv, mat = faces[fi]
        if len(fv) != 4:
            return None
        flat = [a for a in range(3) if max(verts[v][a] for v in fv) - min(verts[v][a] for v in fv) < EPS]
        if len(flat) != 1:
            return None
        a = flat[0]
        at_hi = abs(verts[fv[0]][a] - hi[a]) < EPS
        mats[(("east", "up", "south") if at_hi else ("west", "down", "north"))[a]] = mat
    if set(mats) != {"north", "south", "east", "west", "up", "down"}:
        return None
    return lo, hi, mats


# ------------------------------------------------------------------ writing


def swatch_atlas(colours: dict[str, tuple[int, int, int, int]]):
    """A row of SWATCH-pixel squares, one per material; returns (png bytes, uv per material)."""
    names = sorted(colours)
    width, height = SWATCH * len(names), SWATCH
    rows = [[colours[n] for n in names for _ in range(SWATCH)] for _ in range(SWATCH)]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = Path(f.name)  # write_png only writes to a path
    write_png(tmp, width, height, rows)
    data = tmp.read_bytes()
    tmp.unlink()
    uvs = {n: [i * SWATCH + 1, 1, i * SWATCH + SWATCH - 1, SWATCH - 1] for i, n in enumerate(names)}
    return data, uvs, (width, height)


def to_units(p, drop: float):
    return [p[0] * SCALE, (p[1] - drop) * SCALE, p[2] * SCALE]


def cube_element(name, lo, hi, mats, uvs, drop):
    return {
        "name": name,
        "box_uv": False,
        "rescale": False,
        "locked": False,
        "render_order": "default",
        "allow_mirror_modeling": True,
        "from": to_units(lo, drop),
        "to": to_units(hi, drop),
        "autouv": 0,
        "color": 0,
        "origin": [0, 0, 0],
        "faces": {d: {"uv": uvs[m], "texture": 0} for d, m in mats.items()},
        "type": "cube",
        "uuid": uid("cube", name),
    }


def centre_of(verts, faces, part):
    vs = {v for fi in part for v in faces[fi][0]}
    return tuple(sum(verts[v][a] for v in vs) / len(vs) for a in range(3))


def quarter_turn(p, c):
    """The bundle's tyres face forward; turn a quarter about Y around `c` so the axle runs along X."""
    return (p[2] - c[2] + c[0], p[1], -(p[0] - c[0]) + c[2])


def mesh_element(name, verts, faces, part, uvs, drop, turn_about=None):
    vids = {}
    vertices = {}
    for fi in part:
        for v in faces[fi][0]:
            if v not in vids:
                vids[v] = f"v{len(vids)}"
                p = verts[v] if turn_about is None else quarter_turn(verts[v], turn_about)
                vertices[vids[v]] = to_units(p, drop)
    out_faces = {}
    for k, fi in enumerate(part):
        fv, mat = faces[fi]
        u0, v0, u1, v1 = uvs[mat]
        corners = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]]
        out_faces[f"f{k}"] = {
            "uv": {vids[v]: corners[i % 4] for i, v in enumerate(fv)},
            "vertices": [vids[v] for v in fv],
            "texture": 0,
        }
    return {
        "name": name,
        "box_uv": False,
        "rescale": False,
        "locked": False,
        "render_order": "default",
        "allow_mirror_modeling": True,
        "color": 0,
        "origin": [0, 0, 0],
        "rotation": [0, 0, 0],
        "vertices": vertices,
        "faces": out_faces,
        "type": "mesh",
        "uuid": uid("mesh", name),
    }


def group(name, children):
    g = uid("group", name)
    return (
        {"name": name, "origin": [0, 0, 0], "rotation": [0, 0, 0], "color": 0, "uuid": g,
         "export": True, "mirror_uv": False, "isOpen": True, "locked": False,
         "visibility": True, "autouv": 0, "selected": False},
        {"uuid": g, "isOpen": True, "children": children},
    )


def main() -> None:
    verts, faces, names = read_obj(OBJ)
    colours = read_mtl(MTL)
    drop = min(v[1] for v in verts)
    split = parts(faces)
    if len(split) != len(names):
        raise SystemExit(f"{len(split)} parts but {len(names)} names; the header order cannot be trusted")
    png, uvs, (tw, th) = swatch_atlas(colours)

    by_name = dict(zip(names, split))
    axle_centres = {n[len("wheel_"):]: centre_of(verts, faces, by_name[n]) for n in names if n.startswith("wheel_")}
    elements = []
    round_names = []
    for name, part in zip(names, split):
        cube = as_cube(verts, faces, part)
        if cube:
            elements.append(cube_element(name, *cube, uvs, drop))
        else:
            round_names.append(name)
            side = name.split("_", 1)[1]  # wheel_-1 and hub_-1 turn together about the wheel's centre
            elements.append(mesh_element(name, verts, faces, part, uvs, drop, axle_centres.get(side)))
    expected = {"wheel_-1", "hub_-1", "wheel_1", "hub_1"}
    if set(round_names) != expected:
        raise SystemExit(f"round parts got names {round_names}; expected {sorted(expected)}")

    by_uuid = {e["name"]: e["uuid"] for e in elements}
    wheels = [n for n in names if n.startswith(("wheel_", "hub_"))]
    body = [n for n in names if n not in wheels]
    g_body, o_body = group("body", [by_uuid[n] for n in body])
    g_wheels, o_wheels = group("wheels", [by_uuid[n] for n in wheels])

    project = {
        "meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
        "name": "trailer",
        "model_identifier": "",
        "visible_box": [1, 1, 0],
        "variable_placeholders": "",
        "variable_placeholder_buttons": [],
        "timeline_setups": [],
        "unhandled_root_fields": {},
        "resolution": {"width": tw, "height": th},
        "elements": elements,
        "groups": [g_body, g_wheels],
        "outliner": [o_body, o_wheels],
        "textures": [{
            "name": "trailer_swatches.png", "path": "", "folder": "", "namespace": "", "id": "0",
            "width": tw, "height": th, "uv_width": tw, "uv_height": th, "particle": False,
            "visible": True, "internal": True, "saved": False, "uuid": uid("texture"),
            "source": "data:image/png;base64," + base64.b64encode(png).decode(),
        }],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(project))
    cubes = sum(1 for e in elements if e["type"] == "cube")
    print(f"{OUT.relative_to(Path.cwd())}: {cubes} cubes, {len(elements) - cubes} meshes, "
          f"{len(colours)} swatches, dropped {drop:.2f} blocks")


if __name__ == "__main__":
    main()
