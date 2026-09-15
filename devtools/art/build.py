"""The Trailer's art, as code: nfx's Blockbench project split into what Vanilla Wheels reads, and the profile off it.

Run from the repository root:

    uv run --no-project python devtools/art/build.py

Reads devtools/art/preview/trailer.bbmodel -- nfx's re-creation of the trailer (2026-09-11), as saved -- and writes:

  src/main/resources/assets/trailer/vanillawheels/mesh/trailer.bbmodel        the body: everything but the wheels
  src/main/resources/assets/trailer/vanillawheels/mesh/trailer_wheel.bbmodel  the +X (left) wheel and hub, recentred on the tyre
  src/main/resources/data/trailer/vanillawheels/vehicle/trailer.json          the profile, its numbers measured off the cubes
  src/main/resources/assets/trailer/lang/en_us.json

nfx's build, ported from his handoff; what it does to the model and why:

- The model is built tongue at -Z. The protocol draws +Z forward (hitch.front, forward, the tow geometry),
  so the whole thing is turned half a turn about Y -- a proper rotation: faces keep their winding, north
  and south face UVs swap, east and west too, up and down turn 180, element and group rotations become
  [-rx, ry, -rz], mesh vertices and pivots go (x, y, z) -> (-x, y, -z). After the turn door_rear_left is
  at +X, which is the vehicle's left (facing +Z, +X is on your left).
- The wheels are meshes, not slab stacks; the protocol's reader takes them. The wheel mesh is the +X wheel
  and hub recentred on the tyre's bounding-box centre; the profile spins its own copies at both axle ends.
- Cubes are wrapped into the selector groups the profile names: lenses = the thirty amber rail cubes
  and the four red front lamps and rear reflectors (headlights.part, drawn full-bright when the
  tower's lights are on; with no engine the profile's lamps are point markers),
  glass = the four side windows, paint = the light-grey walls, front panel and roof cap -- not the rear
  doors, since door meshes are drawn untinted.
- parts (at = a box's bottom centre, square footprint, four at most): two wall-wide boxes tiling the shell
  (a seatless vehicle's parts are solid, so nobody walks through the body), a fender-wide box at the axle,
  one on the tongue.
- The door angles are right-hand rotations about +Y: the +X leaf opens with -pi/2, the -X leaf with +pi/2.
  Blockbench's animation keyframes carry the opposite sign to element rotations; never copy one in.

Units are model units, 1/16 block.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

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
    m = json.loads(SRC.read_text(encoding="utf-8"))
    p = Project(m)
    assert all(f.get("texture", 0) == 0 for e in m["elements"] for f in e["faces"].values()), "one texture only"
    m["textures"] = [m["textures"][0]]
    m["textures"][0]["name"] = f"{VEHICLE}.png"
    m["textures"][0]["id"] = "0"
    m.pop("animations", None)  # the protocol swings the doors by the profile
    turn(m)
    assert p.cube("tow_coupler")["to"][2] > 0 and p.cube("rear_step")["from"][2] < 0, "the turn failed: the tongue must be at +Z"

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
    assert len(left) == 2, [wp.els[u]["name"] for u in left]
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

    # The profile, off the cubes.
    def box(name):
        e = p.cube(name)
        return e["from"], e["to"]

    def centre(name, i):
        f, t = box(name)
        return r4((f[i] + t[i]) / 2)

    def group_box(name):
        """effects: returns the bounds (from, to) of every cube in folder name, its subfolders included"""
        uuids = []
        def gather(node):
            for c in node.get("children", []):
                if isinstance(c, str):
                    uuids.append(c)
                else:
                    gather(c)
        gather(p.find_group(m["outliner"], name))
        cubes = [p.els[u] for u in uuids]
        assert cubes, name
        lo = [r4(min(c["from"][i] for c in cubes)) for i in range(3)]
        hi = [r4(max(c["to"][i] for c in cubes)) for i in range(3)]
        return lo, hi

    coupler_f, coupler_t = box("tow_coupler")
    nose = coupler_t[2]
    tail = box("rear_step")[0][2]
    roof_top = box("roof_cap")[1][1]
    roof_w = box("roof_cap")[1][0]
    fender_w = max(abs(box("fender_lower_1")[0][0]), abs(box("fender_lower_1")[1][0]))
    fender_top = box("fender_top_-1")[1][1]
    rail_y = centre(markers[0], 1)
    rail_x = max(abs(v) for v in (box("corr_l_0.02")[0][0], box("corr_l_0.02")[1][0]))
    zs = sorted(centre(n, 2) for n in markers if n.startswith("corr_l_"))
    lamp_z = [zs[1], zs[len(zs) // 2], zs[-2]]
    floor_top = box("interior_floor_mat")[1][1]
    wall_w = max(abs(v) for e in m["elements"] if e["name"].startswith("wall_") for v in (e["from"][0], e["to"][0]))
    front_z = box("front_panel")[1][2]
    rear_z = box("rear_frame_left")[0][2]
    hinge_l = p.group_origin("door_rear_left")
    hinge_r = p.group_origin("door_rear_right")
    assert hinge_l[0] > 0 > hinge_r[0] and hinge_l[2] < 0

    profile = {
        "mesh": f"{MODID}:{VEHICLE}",
        "wheel_mesh": f"{MODID}:{VEHICLE}_wheel",
        "scale": 0.0625,
        "handedness": "right",
        "body": {"width": round(2 * max(roof_w, wall_w) / 16, 2), "length": round((nose - tail) / 16, 2), "height": round(roof_top / 16, 2),
                 "parts": [{"at": [0, 0, r4(front_z - wall_w)], "width": round(2 * wall_w / 16, 2), "height": round(roof_top / 16, 2)},
                           {"at": [0, 0, r4(rear_z + wall_w)], "width": round(2 * wall_w / 16, 2), "height": round(roof_top / 16, 2)},
                           {"at": [0, 0, cz], "width": round(2 * fender_w / 16, 2), "height": round(fender_top / 16, 2)},
                           {"at": [0, coupler_f[1], r4((coupler_f[2] + box("tow_tongue_left")[0][2]) / 2)],
                            "width": round(2 * coupler_t[0] / 16, 2), "height": round((coupler_t[1] - coupler_f[1]) / 16, 2)}]},
        "seats": [],
        "wheels": {"radius": tread, "positions": [{"forward": cz, "right": cx, "up": cy}, {"forward": cz, "right": -cx, "up": cy}]},
        "climb": 1.0,
        "mass": 1.2,
        "hitch": {"front": [0, centre("tow_coupler", 1), nose]},
        "headlights": {"at": [[x, rail_y, z] for x in (-(rail_x + 0.5), rail_x + 0.5) for z in lamp_z],
                       "part": {"group": "lenses"}, "range": MARKER_RANGE},
        "cargo": {"adults": 4, "young": 8,
                  "slots": [[8.8, floor_top, 11], [-8.8, floor_top, 11], [8.8, floor_top, -14], [-8.8, floor_top, -14]]},
        # Each door's box, shut: a crouching click anywhere on it toggles the doors.
        "doors": [{"part": {"group": "door_rear_left"}, "hinge": hinge_l, "axis": [0, 1, 0], "open": -1.5708,
                   "from": group_box("door_rear_left")[0], "to": group_box("door_rear_left")[1]},
                  {"part": {"group": "door_rear_right"}, "hinge": hinge_r, "axis": [0, 1, 0], "open": 1.5708,
                   "from": group_box("door_rear_right")[0], "to": group_box("door_rear_right")[1]}],
        "paint": {"part": {"group": "paint"}, "default": "white"},
        "glass": {"group": "glass"},
    }
    write_json(DATA / "vanillawheels/vehicle" / f"{VEHICLE}.json", profile)
    write_json(ASSETS / "lang/en_us.json", {"vehicle.trailer.trailer": "Trailer"})
    print(f"body {len(body['elements'])} elements; wheel at ({cx}, {cy}, {cz}) radius {tread}; "
          f"{profile['body']['width']} wide {profile['body']['length']} long {profile['body']['height']} high; coupler {profile['hitch']['front']}")


if __name__ == "__main__":
    main()
