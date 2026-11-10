"""
The frame study: one SLS PA12 piece that holds the four motors inside their
ducts, the flight stack, and the posts the canopy (battery, VTX, camera)
screws to. Everything it carries flies with it, so it has no supports:
inertia relief balances each case against the motors, the stack and the
canopy group as rigid bodies at their own centres of mass.

    python frame.py            # writes ../studies/frame.study.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import spec as S

D = S.derived()
A = S.ARM
R_IN = S.DUCT_ID / 2
R_OUT = R_IN + S.DUCT_WALL
# the bumper's inner face: a designable band between the drawn duct skin and the tyre, where the
# optimizer builds whatever ring beam the crash needs (a bare 1.2 mm duct read SF 0.1)
R_SEAT = R_IN + 4.2
SEAT = R_SEAT - R_OUT
Z0, Z1 = S.DUCT_Z
DS_Z = (-6.0, Z1)                  # frame envelope: motor-mount layer below the ducts to the duct tops
STACK_TOP = 19.0                   # canopy seats on the posts here
GRIP = 3.0                         # motor mount: M2 x 6 through 3 mm into the motor's 2.5 mm thread
POSTS = [(24.0, 0.0), (-24.0, 0.0), (0.0, 24.0), (0.0, -24.0)]
MOTORS = [(A, A), (A, -A), (-A, -A), (-A, A)]
MOTOR_BASE_T = 70.0


def S_forced_h():
    from loadpath.cooling import forced_h
    return forced_h(D["wakeVelocity"][0], 20.0, 25.0, MOTOR_BASE_T - 25.0)["h"]
SPIN = [-1, 1, -1, 1]              # sign of the reaction torque about z on the frame (props in)
BUMPER, BUMPER_Z, FOOT = 10.5, -18.5, 12.5   # tyre: 10.5 mm round the duct, a 12.5 mm foot under the frame (bumper.py)
CRASH_SF, FLIGHT_SF = 1.25, 2.0    # a crash may use most of the strength; flight keeps 2 + fatigue


def tube(c, r, r_in, z0, z1):
    return {"type": "tube", "p0": [c[0], c[1], z0], "p1": [c[0], c[1], z1], "r": r, "rInner": r_in}


def box(lo, hi):
    return {"type": "box", "min": list(lo), "max": list(hi)}


def canopy_group():
    """Battery, VTX, camera and the canopy itself: one rigid body on the
    posts. Mass, centre and inertia about the centre (kg mm^2)."""
    parts = [  # kg, centre, box size
        (S.BATTERY["mass"], (-9.0, 0.0, 47.0), S.BATTERY["size"]),
        (S.VTX["mass"], (0.0, 0.0, 25.0), S.VTX["board"]),
        (S.CAMERA["mass"], (36.0, 0.0, 41.0), [26.0, 19.0, 19.0]),
        (0.015, (0.0, 0.0, 30.0), [70.0, 40.0, 25.0]),  # the printed canopy, first guess
    ]
    m = sum(p[0] for p in parts)
    c = sum(p[0] * np.array(p[1]) for p in parts) / m
    j = np.zeros((3, 3))
    for kg, ctr, (a, b, h) in parts:
        jc = kg / 12 * np.diag([b * b + h * h, a * a + h * h, a * a + b * b])
        d = np.array(ctr) - c
        j += jc + kg * (d @ d * np.eye(3) - np.outer(d, d))
    return m, c, j


def study():
    m_motor = S.MOTOR["mass"] + S.PROP["mass"]
    fasteners, motor_faces, motor_seats = [], [], []
    for i, (x, y) in enumerate(MOTORS):
        faces, seats = [], []
        for k, (dx, dy) in enumerate([(1, 1), (1, -1), (-1, -1), (-1, 1)]):
            h = S.MOTOR["boltPattern"] / 2
            fid = f"m{i + 1}{'abcd'[k]}"
            fasteners.append({"id": fid, "size": "M2", "seat": [x + dx * h, y + dy * h, -GRIP], "direction": "+z",
                              "grip": GRIP, "end": "face"})
            faces.append(fid + "-face")
            seats.append(fid + "-seat")
        motor_faces.append(faces)
        motor_seats.append(seats)
    for i, (x, y) in enumerate([(10, 10), (10, -10), (-10, -10), (-10, 10)]):
        fasteners.append({"id": f"s{i + 1}", "size": "M2", "seat": [x, y, 1.5], "direction": "-z", "grip": 0,
                          "end": "thread", "headOn": "mating", "threadLength": 4.0})
    for i, (x, y) in enumerate(POSTS):
        fasteners.append({"id": f"c{i + 1}", "size": "M2", "seat": [x, y, STACK_TOP], "direction": "-z", "grip": 0,
                          "end": "thread", "headOn": "mating", "threadLength": 4.0})

    def union(ids):
        return {"type": "union", "shapes": [{"ref": r} for r in ids]}

    preserve = [{"id": f"duct{i + 1}", "shape": tube(c, R_OUT, R_IN, Z0, Z1)} for i, c in enumerate(MOTORS)]
    keep = []
    for i, (x, y) in enumerate(MOTORS):
        # the prop's disk and the air through the duct above the motor seat
        keep.append({"id": f"air{i + 1}", "bore": False,
                     "shape": {"type": "cylinder", "p0": [x, y, 0.0], "p1": [x, y, 80.0], "r": R_IN}})
        keep.append({"id": f"shaft{i + 1}", "bore": False,
                     "shape": {"type": "cylinder", "p0": [x, y, -20.0], "p1": [x, y, 0.5], "r": 3.5}})
    keep.append({"id": "stack", "bore": False, "insertFrom": "+z",
                 "shape": box([-14.5, -14.5, 1.5], [14.5, 14.5, STACK_TOP])})
    for i, (x, y) in enumerate(MOTORS):
        # the TPU bumper tyre round the duct's exposed arc (outward, +-114 deg)
        u = np.array([np.sign(x), np.sign(y)]) / math.sqrt(2)
        v = np.array([-u[1], u[0]])
        ctr = np.array([x, y]) + u * (65 - 0.4 * R_OUT)
        keep.append({"id": f"bumper{i + 1}", "bore": False, "shape": {"type": "intersect", "shapes": [
            tube((x, y), R_SEAT + BUMPER, R_SEAT, BUMPER_Z, Z1 + 1.5),
            {"type": "box", "center": [ctr[0], ctr[1], 5.0], "size": [130, 130, 60],
             "axes": [[u[0], u[1], 0], [v[0], v[1], 0]]}]}})
    keep.append({"id": "canopy", "bore": False, "shape": box([-42, -42, STACK_TOP], [42, 42, 80])})

    m_c, c_c, j_c = canopy_group()
    m_stack = S.FC["mass"] + S.ESC["mass"] + S.RX["mass"] + S.WIRING["mass"]
    masses = [{"region": None, "shape": None}] * 0
    masses = []
    for i, (x, y) in enumerate(MOTORS):
        masses.append({"shape": {"type": "union", "shapes": [_ring(f) for f in fasteners[4 * i:4 * i + 4]]},
                       "mass": m_motor, "at": [x, y, 8.0], "size": [S.MOTOR["bellDiameter"]] * 2 + [16.0]})
    stack_rings = [_thread(f) for f in fasteners if f["id"].startswith("s")]
    masses.append({"shape": {"type": "union", "shapes": stack_rings}, "mass": m_stack, "at": [0.0, 0.0, 10.0],
                   "size": [27.0, 27.0, 16.0]})
    post_rings = [_thread(f) for f in fasteners if f["id"].startswith("c")]
    masses.append({"shape": {"type": "union", "shapes": post_rings}, "mass": round(m_c, 4),
                   "at": [round(v, 2) for v in c_c], "inertia": np.round(j_c, 2).tolist()})

    t_full, t_idle = D["maxThrustPerMotor"], 0.3
    q_full = D["motorTorqueNm"][1] * 1000.0          # N mm

    def motor_loads(thrusts):
        out = []
        for i, t in enumerate(thrusts):
            q = q_full * (t / t_full) ** 1.5 if t > 0 else 0.0
            out.append({"shape": _union_rings(fasteners[4 * i:4 * i + 4], "seat"), "force": [0, 0, round(t, 3)]})
            if t > 1.0:     # idle reaction torque (under 1 N mm) is nothing
                out.append({"shape": _union_rings(fasteners[4 * i:4 * i + 4], "face"),
                            "moment": [0, 0, round(SPIN[i] * q, 2)]})
        return out

    k = 1.0       # crash cases carry their own safetyFactor (CRASH_SF)
    # the crash forces are what the bumper actually lets through (bumper.py)
    bump = json.loads((Path(__file__).resolve().parents[1] / "studies" / "bumper.json").read_text())
    wall = bump["wall"]["peakForce"] * k
    drop = bump["drop"]["peakForce"] * k
    x, y = MOTORS[0]
    # a bumper spreads the hit over the arc it crushes: 2 sqrt(2 R delta)
    arc = 2 * math.sqrt(2 * (R_SEAT + BUMPER) * bump["wall"]["crush"])

    def patch(direction, z0=Z0, z1=Z1):
        u = np.array(direction, float) / np.linalg.norm(direction)
        p = np.array([x, y]) + u * R_SEAT
        half = arc / 2
        # the tyre bears on the duct and whatever the design builds in the seat band behind it
        return {"type": "intersect", "shapes": [tube((x, y), R_SEAT + 0.01, R_IN - 0.01, z0, z1),
                                                {"type": "cylinder", "p0": [p[0], p[1], z0 - 1],
                                                 "p1": [p[0], p[1], z1 + 1], "r": half}]}

    def patch_point(direction):
        u = np.array(direction, float) / np.linalg.norm(direction)
        p = np.array([x, y]) + u * R_SEAT
        return np.array([p[0], p[1], 0.5 * (Z0 + Z1)])

    def to_cg(p):
        cg = all_cg()
        d = cg - p
        return d / np.linalg.norm(d)

    def all_cg():
        parts = [(m_motor, np.array([mx, my, 8.0])) for mx, my in MOTORS]
        parts += [(m_stack, np.array([0.0, 0.0, 10.0])), (m_c, np.array(c_c)),
                  (S.FRAME_MASS_BUDGET, np.array([0.0, 0.0, 9.0]))]
        return sum(k * c for k, c in parts) / sum(k for k, _ in parts)

    def hit(which):
        # the bumper and the frame behind it are springs in series: the frame's own give at the
        # patch shares the energy, the force is solved, not assumed (loadpath impact cases)
        c = bump[which]["curve"]
        return {"velocity": bump[which]["speed"], "crusher": {"distance": c["distance"], "force": c["force"]}}

    s2 = math.sqrt(0.5)
    cases = [
        {"name": "punch", "loads": motor_loads([t_full] * 4), "cycles": 1e5},
        {"name": "roll", "loads": motor_loads([t_full, t_full, t_idle, t_idle][::1]), "cycles": 1e5},
        {"name": "yaw", "loads": motor_loads([t_full, t_idle, t_full, t_idle]), "cycles": 1e5},
        {"name": "corner", "loads": motor_loads([t_full, t_idle, t_idle, t_idle])},
        {"name": "wall-front", "safetyFactor": CRASH_SF, "loads": [{"shape": patch([1, 0]), "force": [-round(wall, 1), 0, 0]}],
         "impact": hit("wall")},
        {"name": "wall-corner", "safetyFactor": CRASH_SF, "loads": [{"shape": patch([s2, s2]), "force": [-round(wall * s2, 1),
                                                                               -round(wall * s2, 1), 0]}],
         "impact": hit("wall")},
        {"name": "drop-corner", "safetyFactor": CRASH_SF, "loads": [{"shape": patch([s2, s2], Z0, Z0 + 3), "force": [0, 0, round(drop, 1)]}],
         "impact": hit("drop")},
        # the worst attitude for one tyre: tumbling so the line of the hit runs through the centre of
        # mass; then the patch stops all of the drone and the full 2 m drop energy (a flat drop on a
        # corner stops ~15% and the rest stays as spin for the next contacts)
        {"name": "drop-cg", "safetyFactor": CRASH_SF,
         "loads": [{"shape": patch([s2, s2]), "force": [round(v * drop, 1) for v in to_cg(patch_point([s2, s2]))]}],
         "impact": hit("drop")},
    ]
    return {
        "name": "hum-frame",
        "description": "3.5 in ducted quad frame, SLS PA12: ducts, motor mounts, stack floor, canopy posts. "
                       "Loads from hum/src/spec.py: full-throttle punch, roll, yaw and single-motor cases with "
                       "motor reaction torque; crash and drop forces as the TPU bumper lets them through (bumper.py), held "
                       f"to SF {CRASH_SF} (flight cases to {FLIGHT_SF}).",
        "designSpace": box([-A - R_SEAT - 0.5, -A - R_SEAT - 0.5, DS_Z[0]], [A + R_SEAT + 0.5, A + R_SEAT + 0.5, DS_Z[1]]),
        "preserve": preserve,
        "keepOut": keep,
        "fasteners": fasteners,
        "inertiaRelief": {"masses": masses},
        "loadCases": cases,
        "material": S.FRAME_MATERIAL,
        "process": S.FRAME_PROCESS,
        "goal": {"safetyFactor": FLIGHT_SF},
        "vibration": {"minFrequency": D["minFrequency"], "modes": 6},
        # every gram of structure in a prop's stream costs thrust: drag / g counts as carried mass
        # motor bases run hot after a hard pack (stator 60-80 C, base ~70 C); the hover wake
        # (2 v_i ~ 14 m/s over a 20 mm arm) cools the rest at h ~ 110 W/m^2K (cooling.forced_h)
        "thermal": {"ambient": 25.0, "convection": round(S_forced_h(), 0),
                    "temperatures": [{"region": f, "t": MOTOR_BASE_T} for fs in motor_faces for f in fs]},
        "aero": {"rotors": [{"name": f"m{i + 1}", "center": [x, y, S.PROP_Z], "axis": "-z",
                             "radius": S.PROP["diameter"] / 2, "hub": 14.0,
                             "thrust": D["hoverThrustPerMotor"], "ducted": True}
                            for i, (x, y) in enumerate(MOTORS)]},
        "symmetry": ["x", "y"],
        "durability": {"temperature": 50},
        "minMember": 2.4,
        "resolution": {"pitch": 1.5},
    }


def _ring(f):
    """The motor-side ring of a motor screw (its `face`)."""
    x, y, z = f["seat"]
    return {"type": "tube", "p0": [x, y, -0.6], "p1": [x, y, 0.0], "r": 2.9, "rInner": 1.1}


def _union_rings(fs, which):
    out = []
    for f in fs:
        x, y, z = f["seat"]
        z0, z1 = (z, z + 0.6) if which == "seat" else (-0.6, 0.0)
        out.append({"type": "tube", "p0": [x, y, z0], "p1": [x, y, z1], "r": 2.9, "rInner": 1.1})
    return {"type": "union", "shapes": out}


def _thread(f):
    x, y, z = f["seat"]
    return {"type": "tube", "p0": [x, y, z - 4.0], "p1": [x, y, z], "r": 2.5, "rInner": 0.85}


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "studies" / "frame.study.json"
    out.write_text(json.dumps(study(), indent=1) + "\n")
    m, c, j = canopy_group()
    print(out, f"canopy group {m:.3f} kg at {np.round(c, 1)}")
