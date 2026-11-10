"""
The duct bumper: a TPU gyroid tyre round each duct's exposed arc that stops
the crashes the frame is designed for. Its job, from spec.py: a 4 m/s wall
hit (2.5 J) under 395 N, and a 2 m drop (6.2 J) under 969 N, in 8 mm of
crush, and spring back for the next one.

loadpath's impact model crushes the tyre's cap in layers along the hit (the
cap is what lies in front of the duct; the duct behind it is the anvil) and
grades the gyroid's density layer by layer so every layer crushes at about
the same force.

    python bumper.py          # prints both crashes; writes ../studies/bumper-*.json
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import spec as S
from frame import BUMPER, BUMPER_Z, FOOT, R_OUT, A
from loadpath.fields import FieldGraph
from loadpath.impact import impact_report
from loadpath.materials import material_from_spec

D = S.derived()
MAT = "tpu"                       # FDM TPU 95A: single 0.45 mm lines let the gyroid go soft enough
CELL, MIN_WALL = 7.0, 0.45         # one 0.45 mm extrusion line per wall
R2 = R_OUT + BUMPER


def tyre_cap(axis):
    """The tyre of the duct at (A, A), cut to the cap in front of the duct
    along +x (wall hit) or under it along -z (drop)."""
    ring = (f"max(max({R_OUT} - r, r - {R2}), max({BUMPER_Z} - z, z - {S.DUCT_Z[1]}))")
    r = f"sqrt((x - {A}) * (x - {A}) + (y - {A}) * (y - {A}))"
    if axis == "x":
        expr = f"max({ring}, {A + R_OUT} - x)"
        lo, hi = [A + R_OUT - 0.5, A - 40, BUMPER_Z], [A + R2 + 0.5, A + 40, S.DUCT_Z[1]]
    else:
        # the drop lands on the tyre's foot: the 8 mm under the frame's lowest point
        ring = f"max(max({R_OUT} - r, r - {R2}), max({BUMPER_Z} - z, z - ({BUMPER_Z} + {FOOT})))"
        expr = ring
        lo, hi = [A - R2 - 0.5, A - R2 - 0.5, BUMPER_Z], [A + R2 + 0.5, A + R2 + 0.5, BUMPER_Z + FOOT]
    return {"op": "expr", "expr": expr.replace("r", "rr").replace("max", "max").replace("rr -", "rr -"),
            "vars": {}, "bounds": {"min": lo, "max": hi}, "_r": r}


def graph(axis, density=0.3):
    env = tyre_cap(axis)
    r = env.pop("_r")
    env["expr"] = env["expr"].replace("rr", "r")
    env["vars"] = {"r": {"op": "expr", "expr": r}}
    return {"name": f"bumper-{axis}", "nodes": {
        "envelope": env,
        "density": {"op": "constant", "value": density},
        "core": {"op": "lattice", "type": "gyroid", "cell": CELL, "density": "density"},
        "part": {"op": "intersect", "inputs": ["core", "envelope"]}},
        "output": "part", "material": MAT, "process": "fdm"}


def crash(axis, mass, velocity, limit):
    doc = graph(axis)
    spec = {"envelope": "envelope", "density": "density", "lattice": "gyroid", "axis": "x" if axis == "x" else "z",
            "mass": mass, "velocity": velocity, "forceLimit": limit, "pitch": 0.5, "grade": True,
            "cell": CELL, "minWall": MIN_WALL}
    mat = material_from_spec(MAT)
    first = impact_report(FieldGraph(doc), spec, mat)
    g = copy.deepcopy(doc)
    g["nodes"]["density"] = first["graded"]["density"]
    graded = impact_report(FieldGraph(g), {**spec, "grade": False}, mat)
    g["impact"] = {**spec, "grade": False}
    return first, graded, g


if __name__ == "__main__":
    m = D["allUpMass"]
    here = Path(__file__).resolve().parents[1] / "studies"
    summary = {}
    for name, axis, v, lim in (("wall", "x", D["wallCrash"]["speed"], D["wallCrash"]["peakForce"]),
                               ("drop", "z", D["drop"]["speed"], D["drop"]["peakForce"])):
        first, graded, doc = crash(axis, m, v, lim)
        print(name, "uniform 0.3:", json.dumps(first["response"]), "ok", first.get("ok"))
        print(name, "graded:", json.dumps(graded["response"]), "ok", graded.get("ok"), "core", graded["coreMass"], "g")
        (here / f"bumper-{name}.json").write_text(json.dumps(doc, indent=1) + "\n")
        summary[name] = {"speed": v, "energyJ": round(graded["energy"] / 1000, 3), "limit": lim,
                         "peakForce": graded["response"]["peakForce"], "crush": graded["response"]["crush"],
                         "efficiency": graded["response"]["efficiency"], "coreMass": graded["coreMass"],
                         "rebound": graded.get("reboundEnergy"), "ok": graded.get("ok")}
    (here / "bumper.json").write_text(json.dumps(summary, indent=1) + "\n")
