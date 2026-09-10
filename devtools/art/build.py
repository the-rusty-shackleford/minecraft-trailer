"""The Trailer's art, as code: the generated bundle normalized into what Vanilla Wheels reads.

Run from the repository root:

    uv run --no-project python devtools/art/build.py

Reads the generator's OBJ and MTL from devtools/art/src/ (committed as they
came, see SOURCES.md there), and writes:

  src/main/resources/assets/trailer/vanillawheels/mesh/trailer.obj
  src/main/resources/assets/trailer/vanillawheels/mesh/trailer_wheel.obj
  src/main/resources/assets/trailer/textures/entity/trailer.png
  src/main/resources/data/trailer/vanillawheels/vehicle/trailer.json
  src/main/resources/assets/trailer/lang/en_us.json

What it changes, and why (measured on the bundle):

- The OBJ declares its 86 group names in a header and never attaches them
  to faces, so every face reads as the last group. The four parts the
  protocol must find -- the two wheels with their hubs and the two rear
  doors -- are named again by their geometry; nothing else needs a name.
- The bundle's front is -Z; Vanilla Wheels' is +Z. The mesh is turned half
  a turn about Y (which keeps its handedness), and dropped so the tyres
  touch y = 0.
- The wheels are part of the frame; the protocol draws its own at the
  wheel positions and spins them. The left wheel and hub are cut out into
  the wheel mesh about their own centre, turned a quarter turn so the axle
  runs across the vehicle (the bundle's tyres face forward and would roll
  sideways), and all four wheels leave the frame.
- There is no texture and no UV: an atlas of swatches is made from the
  MTL colours (the body ones in grey so a dye colours them, the glass with
  alpha), and every face is given coordinates inside its swatch.

Units are blocks, so the profile's scale is 1.
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent / "src"
MODID = "trailer"
ASSETS = ROOT / "src/main/resources/assets" / MODID
DATA = ROOT / "src/main/resources/data" / MODID


# ---------------------------------------------------------------- PNG writing

def write_png(path: Path, width: int, height: int, pixels) -> None:
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


class Noise:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / 0xFFFFFFFF


# ---------------------------------------------------------------- the mesh

class Face:
    __slots__ = ("material", "group", "corners")

    def __init__(self, material, group, corners):
        self.material = material
        self.group = group
        self.corners = corners


def read_mtl(path: Path):
    colours = {}
    name = None
    for line in path.read_text().splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "newmtl":
            name = t[1]
        elif t[0] == "Kd" and name:
            colours[name] = tuple(int(round(float(c) * 255)) for c in t[1:4])
    return colours


def read_obj(path: Path):
    """The faces with their materials. The header's group names are not attached to faces (see below)."""
    v, faces, material = [], [], None
    for line in path.read_text().splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            v.append(tuple(float(c) for c in t[1:4]))
        elif t[0] == "usemtl":
            material = t[1]
        elif t[0] == "f":
            faces.append(Face(material, "frame", [v[int(c.split("/")[0]) - 1] for c in t[1:]]))
    return faces


def pieces(faces):
    """Faces grouped into connected pieces (shared vertex coordinates)."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for f in faces:
        keys = [tuple(round(c, 4) for c in p) for p in f.corners]
        for k in keys[1:]:
            ra, rb = find(keys[0]), find(k)
            if ra != rb:
                parent[ra] = rb
    groups = defaultdict(list)
    for f in faces:
        groups[find(tuple(round(c, 4) for c in f.corners[0]))].append(f)
    return list(groups.values())


def name_parts(faces):
    """
    Puts the group names the protocol selects by on the parts that need
    them, found by their geometry in the bundle's frame: the tyres (16-gon
    prisms of 48 faces, material tire), the hubs (36, hub), and the two rear
    doors (body-material boxes on the rear face, z 2.31..2.38, one each
    side of the centreline). Everything else stays "frame".
    """
    for piece in pieces(faces):
        mats = {f.material for f in piece}
        lo, hi = bounds(piece)
        cx = (lo[0] + hi[0]) / 2
        side = "-1" if cx < 0 else "1"
        if mats == {"tire"} and len(piece) == 48:
            name = "wheel_" + side
        elif mats == {"hub"} and len(piece) == 36:
            name = "hub_" + side
        elif mats == {"body"} and len(piece) == 6 and 2.3 <= lo[2] and hi[2] <= 2.4 and hi[1] - lo[1] > 1.0:
            name = "rear_door_left" if cx < 0 else "rear_door_right"
        else:
            continue
        for f in piece:
            f.group = name


def turn(p):
    """Half a turn about Y, and down so the tyres meet the ground."""
    return (-p[0], p[1] - GROUND, -p[2])


GROUND = 0.2
WHEEL_GROUPS = {"wheel_-1", "hub_-1", "wheel_1", "hub_1"}
LEFT_WHEEL = {"wheel_-1", "hub_-1"}


# ---------------------------------------------------------------- the atlas

CELL = 32
GRID = 4
PAINT_GREY = {"body": 240, "body_dark": 197, "body_highlight": 255}
GLASS_ALPHA = 150
INSET = 0.06


def cells(materials):
    return {m: (i % GRID, i // GRID) for i, m in enumerate(sorted(materials))}


def atlas(materials, colours):
    noise = Noise(0x7A11)
    px = [[(0, 0, 0, 0) for _ in range(CELL * GRID)] for _ in range(CELL * GRID)]
    for m, (cx, cy) in cells(materials).items():
        base = (PAINT_GREY[m],) * 3 if m in PAINT_GREY else colours.get(m, (200, 0, 200))
        alpha = GLASS_ALPHA if m == "glass" else 255
        for y in range(CELL):
            for x in range(CELL):
                d = int((noise.next() - 0.5) * 14)
                px[cy * CELL + y][cx * CELL + x] = (*tuple(max(0, min(255, c + d)) for c in base), alpha)
    return px


# ---------------------------------------------------------------- writing

def face_uvs(n):
    """Swatch coordinates for a face of n corners: the four corners of the swatch, inset, for a quad; the centre for anything else."""
    if n == 4:
        return [(INSET, INSET), (1 - INSET, INSET), (1 - INSET, 1 - INSET), (INSET, 1 - INSET)]
    return [(0.5, 0.5)] * n


def write_obj(path: Path, faces, cell_of, note: str):
    lines = [f"# {note}", "# generated by devtools/art/build.py; the source bundle is under devtools/art/src"]
    v_index, vs, vt_index, vts = {}, [], {}, []
    by_group = defaultdict(list)
    for f in faces:
        by_group[(f.group, f.material)].append(f)
    for (g, m), fs in by_group.items():
        cx, cy = cell_of[m]
        for f in fs:
            for (x, y, z), (fu, fv) in zip(f.corners, face_uvs(len(f.corners))):
                k = (round(x, 4), round(y, 4), round(z, 4))
                if k not in v_index:
                    v_index[k] = len(vs) + 1
                    vs.append(k)
                t = (round((cx + fu) / GRID, 5), round(1.0 - (cy + 1 - fv) / GRID, 5))
                if t not in vt_index:
                    vt_index[t] = len(vts) + 1
                    vts.append(t)
    for x, y, z in vs:
        lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
    for u, w in vts:
        lines.append(f"vt {u:.5f} {w:.5f}")
    for (g, m), fs in by_group.items():
        cx, cy = cell_of[m]
        lines.append(f"g {g}")
        lines.append(f"usemtl {m}")
        for f in fs:
            ref = []
            for (x, y, z), (fu, fv) in zip(f.corners, face_uvs(len(f.corners))):
                vi = v_index[(round(x, 4), round(y, 4), round(z, 4))]
                ti = vt_index[(round((cx + fu) / GRID, 5), round(1.0 - (cy + 1 - fv) / GRID, 5))]
                ref.append(f"{vi}/{ti}")
            lines.append("f " + " ".join(ref))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def bounds(faces):
    pts = [p for f in faces for p in f.corners]
    return tuple(min(p[k] for p in pts) for k in range(3)), tuple(max(p[k] for p in pts) for k in range(3))


# ---------------------------------------------------------------- the profile

def profile(wheel_centre, wheel_radius):
    return {
        "mesh": "trailer:trailer",
        "wheel_mesh": "trailer:trailer_wheel",
        "texture": "trailer:textures/entity/trailer.png",
        "scale": 1.0,
        "handedness": "right",
        "body": {"width": 2.4, "length": 5.2, "height": 2.1,
                 "parts": [{"at": [0, 0.25, -0.45], "width": 2.3, "height": 1.95}, {"at": [0, 0.15, 2.0], "width": 0.6, "height": 0.4}]},
        "seats": [],
        "wheels": {"radius": round(wheel_radius, 3),
                   "positions": [{"forward": round(wheel_centre[2], 3), "right": -round(abs(wheel_centre[0]), 3)},
                                 {"forward": round(wheel_centre[2], 3), "right": round(abs(wheel_centre[0]), 3)}]},
        "climb": 2.0,
        "mass": 1.2,
        "hitch": {"front": [0, 0.42 - GROUND, 2.6]},
        "cargo": {"adults": 4, "young": 8, "slots": [[0.55, 0.32, 0.6], [-0.55, 0.32, 0.6], [0.55, 0.32, -1.4], [-0.55, 0.32, -1.4]]},
        # The doors are hinged on the body's rear corners and swing out and back, about two thirds of a turn.
        "doors": [{"part": {"group": "rear_door_left"}, "hinge": [0.96, 1.25, -2.34], "axis": [0, 1, 0], "open": -1.9},
                  {"part": {"group": "rear_door_right"}, "hinge": [-0.96, 1.25, -2.34], "axis": [0, 1, 0], "open": 1.9}],
        "paint": {"part": {"material": ["body", "body_dark", "body_highlight"]}, "default": "white"},
        "glass": {"material": "glass"},
    }


def main(argv) -> None:
    colours = read_mtl(SRC / "trailblazer_animal_trailer.mtl")
    faces = read_obj(SRC / "trailblazer_animal_trailer.obj")
    name_parts(faces)
    for f in faces:
        f.corners = [turn(p) for p in f.corners]
    wheel = [f for f in faces if f.group in LEFT_WHEEL]
    frame = [f for f in faces if f.group not in WHEEL_GROUPS]
    lo, hi = bounds([f for f in wheel if f.group == "wheel_-1"])
    centre = tuple((lo[k] + hi[k]) / 2 for k in range(3))
    radius = (hi[1] - lo[1]) / 2
    for f in wheel:
        # About its own centre, then a quarter turn about Y: the bundle's tyre is a disc facing
        # forward (its axle along Z), and a wheel's axle runs across the vehicle, along X.
        f.corners = [(p[2] - centre[2], p[1] - centre[1], -(p[0] - centre[0])) for p in f.corners]
    materials = sorted(set(colours) | {f.material for f in faces})
    cell_of = cells(materials)
    write_obj(ASSETS / "vanillawheels/mesh/trailer.obj", frame, cell_of, "The Trailer, blocks, +Z forward, right-handed")
    write_obj(ASSETS / "vanillawheels/mesh/trailer_wheel.obj", wheel, cell_of, "The Trailer's wheel, blocks, axle along X")
    write_png(ASSETS / "textures/entity/trailer.png", CELL * GRID, CELL * GRID, atlas(materials, colours))
    write_json(DATA / "vanillawheels/vehicle/trailer.json", profile(centre, radius))
    write_json(ASSETS / "lang/en_us.json", {"vehicle.trailer.trailer": "Trailer"})
    flo, fhi = bounds(frame)
    print(f"wrote the trailer ({len(frame)} faces, x {flo[0]:.2f}..{fhi[0]:.2f} y {flo[1]:.2f}..{fhi[1]:.2f} z {flo[2]:.2f}..{fhi[2]:.2f}),"
          f" the wheel ({len(wheel)} faces, centre {tuple(round(c, 3) for c in centre)}, radius {radius:.3f}), {len(materials)} swatches")


if __name__ == "__main__":
    main(sys.argv)
