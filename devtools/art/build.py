"""Import the approved cosmetic Blockbench derivative without changing gameplay.

Run with --appearance-only. The released profile and original model are retained in
reference/. The profile is checked before import and is never regenerated from artwork.
This preserves nfx's rig and the existing gameplay while allowing deliberate art edits.
Copyright 2026 Rusty Shackleford and nfx. SPDX-License-Identifier: AGPL-3.0-or-later.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from appearance import require_appearance_only

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "devtools/art/preview/trailer.bbmodel"
MODID = "trailer"
VEHICLE = "trailer"
ASSETS = ROOT / "src/main/resources/assets" / MODID
DATA = ROOT / "src/main/resources/data" / MODID
MESH = ASSETS / "vanillawheels/mesh"
# Blocks the side lamps reach: an unpowered vehicle's lamps are points of luminance twice the range.
MARKER_RANGE = 3


def r4(v):
    return round(v, 4)


# ---------------------------------------------------------------- the half turn

def turn(model):
    """effects: rotates the whole model half a turn about Y: (x, y, z) -> (-x, y, -z), a proper rotation"""
    swap = {"north": "south", "south": "north", "east": "west", "west": "east"}
    for e in model["elements"]:
        if e.get("type", "cube") == "cube":
            f, t = e["from"], e["to"]
            e["from"], e["to"] = [r4(-t[0]), f[1], r4(-t[2])], [r4(-f[0]), t[1], r4(-f[2])]
            e["faces"] = {swap.get(k, k): v for k, v in e["faces"].items()}
            for k in ("up", "down"):
                if k in e["faces"]:
                    e["faces"][k]["rotation"] = (e["faces"][k].get("rotation", 0) + 180) % 360
        else:  # a mesh: vertices are relative to the origin
            e["vertices"] = {k: [r4(-v[0]), v[1], r4(-v[2])] for k, v in e["vertices"].items()}
        o = e.get("origin", [0, 0, 0])
        e["origin"] = [r4(-o[0]), o[1], r4(-o[2])]
        r = e.get("rotation")
        if r:
            e["rotation"] = [r4(-r[0]), r[1], r4(-r[2])]  # R_y(180) R(rx, ry, rz) = R(-rx, ry, -rz) R_y(180)
    for g in model["groups"]:
        o = g.get("origin", [0, 0, 0])
        g["origin"] = [r4(-o[0]), o[1], r4(-o[2])]
        r = g.get("rotation")
        if r:
            g["rotation"] = [r4(-r[0]), r[1], r4(-r[2])]


# ---------------------------------------------------------------- the outliner

class Project:
    def __init__(self, model):
        self.m = model
        self.gname = {g["uuid"]: g["name"] for g in model["groups"]}
        self.els = {e["uuid"]: e for e in model["elements"]}

    def strip(self, names):
        """effects: drops the named top-level folders with everything in them"""
        drop = set()

        def collect(n):
            if isinstance(n, str):
                drop.add(n)
                return
            drop.add(n["uuid"])
            for c in n.get("children", []):
                collect(c)

        keep = []
        for n in self.m["outliner"]:
            if not isinstance(n, str) and self.gname[n["uuid"]] in names:
                collect(n)
            else:
                keep.append(n)
        self.m["outliner"] = keep
        self.m["groups"] = [g for g in self.m["groups"] if g["uuid"] not in drop]
        self.m["elements"] = [e for e in self.m["elements"] if e["uuid"] not in drop]

    def find_group(self, nodes, name):
        for n in nodes:
            if isinstance(n, str):
                continue
            if self.gname[n["uuid"]] == name:
                return n
            r = self.find_group(n.get("children", []), name)
            if r:
                return r
        return None

    def wrap(self, parent_name, new_name, cube_names):
        """effects: moves the named cubes of folder parent_name into a new child folder new_name"""
        parent = self.find_group(self.m["outliner"], parent_name)
        assert parent, parent_name
        wanted = {u for u in parent["children"] if isinstance(u, str) and self.els[u]["name"] in cube_names}
        missing = set(cube_names) - {self.els[u]["name"] for u in wanted}
        assert not missing, (parent_name, sorted(missing))
        uuid = f"{new_name}-{parent_name}-0000-0000-000000000000"
        node = {"uuid": uuid, "isOpen": False, "children": [u for u in parent["children"] if isinstance(u, str) and u in wanted]}
        parent["children"] = [u for u in parent["children"] if not (isinstance(u, str) and u in wanted)] + [node]
        self.m["groups"].append({"name": new_name, "uuid": uuid, "origin": [0, 0, 0], "rotation": [0, 0, 0], "export": True,
                                 "visibility": True, "autouv": 0, "selected": False, "shade": True, "mirror_uv": False,
                                 "isOpen": False, "locked": False, "color": 0})
        self.gname[uuid] = new_name

    def cube(self, name):
        r = [e for e in self.m["elements"] if e["name"] == name]
        assert len(r) == 1, (name, len(r))
        return r[0]

    def group_origin(self, name):
        return [g for g in self.m["groups"] if g["name"] == name][0]["origin"]


def write_json(path: Path, data, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, separators=(",", ":")) if compact else json.dumps(data, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    profile_path = DATA / "vanillawheels/vehicle/trailer.json"
    profile_bytes = require_appearance_only(profile_path, ROOT / "devtools/art/reference/released-profile.json")
    m = json.loads(SRC.read_text(encoding="utf-8"))
    p = Project(m)
    assert all(f.get("texture", 0) == 0 for e in m["elements"] for f in e["faces"].values()), "one texture only"
    m["textures"] = [m["textures"][0]]
    m["textures"][0]["name"] = f"{VEHICLE}.png"
    m["textures"][0]["id"] = "0"
    m.pop("animations", None)  # the protocol swings the doors by the profile
    turn(m)
    assert p.cube("tow_coupler")["to"][2] > 0 and p.cube("rear_door_left")["from"][2] < 0, "the turn failed: the tongue must be at +Z"

    names = [e["name"] for e in m["elements"]]
    markers = sorted(n for n in names if n.startswith("corr_"))
    assert len(markers) == 30, len(markers)
    # The lamps that glow with the tower's lights: the thirty amber rail markers, the two red
    # front lamps and the two red rear reflectors (Rusty: "the little yellow siding lights and
    # the red lights on the front and rear of the trailer").
    p.wrap("body", "lenses", markers + ["front_lamp_left", "front_lamp_right"])
    # The rear reflectors ride on the doors, so their lens folders sit inside the door folders: the
    # selector matches a group by any component of its path, and a door draws its own lenses.
    p.wrap("door_rear_left", "lenses", ["rear_reflector_left"])
    p.wrap("door_rear_right", "lenses", ["rear_reflector_right"])
    p.wrap("body", "glass", [n for n in names if n.startswith("side_window")])
    paint = ["front_panel", "wall_lower_front", "wall_lower_left", "wall_lower_right", "wall_upper_front",
             "wall_upper_left_low", "wall_upper_left_high", "wall_upper_left_fwd", "wall_upper_left_mid", "wall_upper_left_aft",
             "wall_upper_right_low", "wall_upper_right_high", "wall_upper_right_fwd", "wall_upper_right_mid", "wall_upper_right_aft",
             "roof_cap"]
    paint.extend(n for n in names if n.startswith("panel_bead_"))
    p.wrap("body", "paint", paint)

    # The body: everything but the wheels.
    body = copy.deepcopy(m)
    Project(body).strip({"wheels"})
    body["name"] = VEHICLE
    body["model_identifier"] = VEHICLE
    write_json(MESH / f"{VEHICLE}.bbmodel", body, compact=True)

    # The wheel: the +X (left) mesh wheel and hub, recentred on the tyre.
    wheel = copy.deepcopy(m)
    wp = Project(wheel)
    wp.strip({wp.gname[x["uuid"]] for x in wheel["outliner"] if not isinstance(x, str)} - {"wheels"})
    wg = [n for n in wheel["outliner"] if not isinstance(n, str)][0]

    def verts(e):
        return [[e["origin"][i] + v[i] for i in range(3)] for v in e["vertices"].values()]

    left = [u for u in wg["children"] if isinstance(u, str) and min(pt[0] for pt in verts(wp.els[u])) > 0]
    assert len(left) >= 2, [wp.els[u]["name"] for u in left]
    wg["children"] = left
    wheel["elements"] = [wp.els[u] for u in left]
    wheel["groups"] = [g for g in wheel["groups"] if g["name"] == "wheels"]
    tyre = [e for e in wheel["elements"] if e["name"].startswith("wheel")][0]
    pts = verts(tyre)
    cx = r4((min(q[0] for q in pts) + max(q[0] for q in pts)) / 2)
    cy = r4((min(q[1] for q in pts) + max(q[1] for q in pts)) / 2)
    cz = r4((min(q[2] for q in pts) + max(q[2] for q in pts)) / 2)
    tread = r4(max(q[1] for q in pts) - cy)
    for e in wheel["elements"]:
        e["origin"] = [r4(e["origin"][0] - cx), r4(e["origin"][1] - cy), r4(e["origin"][2] - cz)]
    for g in wheel["groups"]:
        g["origin"] = [0, 0, 0]
    wheel["name"] = f"{VEHICLE}_wheel"
    wheel["model_identifier"] = f"{VEHICLE}_wheel"
    write_json(MESH / f"{VEHICLE}_wheel.bbmodel", wheel, compact=True)

    assert profile_path.read_bytes() == profile_bytes
    print(f"appearance-only: {len(body['elements'])} body elements, {len(wheel['elements'])} wheel elements; gameplay profile unchanged")


if __name__ == "__main__":
    main()
