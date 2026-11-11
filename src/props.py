"""
hum's rotors, designed with loadpath.propeller on the motor and pack in spec.py.

Three rotors compete on electrical watts at hover, each designed for the least
watts that still meet the mission's full-throttle thrust (spec.required_full_thrust),
on the flexing printed blade (PA12 SLS, 0.8 mm thinnest wall):

- open-89: an open 3.5 in rotor (89 mm), the size the ducted frame was drawn round;
- ducted-89: the same rotor inside the frame's duct (aero.duct_performance: 1 mm tip gap,
  6.5 mm lip radius, 16 mm below the disk); the blade carries the rotor's share of
  thrust at the duct's disk velocity, and the duct's own losses are added to its power;
- open-100: the largest open rotor the 104 mm motor spacing leaves room for (2 mm apart).

Writes ../out/props/props.json and the winning blade as STL in both hands.
Run: python props.py   (needs loadpath[aero])
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)
sys.path.insert(0, str(Path(__file__).parent))

import spec  # noqa: E402
from loadpath import aero, propeller as pr  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out" / "props"
R_HUB = 7.0                                   # hub ring radius: 5 mm shaft bore, 4.5 mm of wall round it
MATERIAL = "pa12"
T_MIN = 0.8                                   # SLS PA12's thinnest reliable wall (Materialize)
HUB_H = spec.PROP["hubHeight"]                # the hub the motor's M5 shaft takes (an off-the-shelf 3.5 in prop's): roots neck to fit


def kit():
    m = spec.MOTOR
    b = spec.BATTERY
    motor = pr.Motor(m["kv"], m["rm"], m["i0"], m["maxCurrent"], m["mass"], m["rotorInertia"])
    pack = pr.Battery(b["cells"], b["cellVolts"], b["cellOhms"])
    return motor, pack


def duct_for(r_tip, thrust):
    return aero.duct_performance(r_tip, thrust, tip_gap=spec.TIP_GAP, lip_radius=6.5, length=16.0,
                                 outer_radius=r_tip + spec.TIP_GAP + 4.2, hub=R_HUB)


def summarise(name, rec, extra=None):
    e = rec["evaluation"]
    h, f = e["hover"], e["full"]
    out = {"name": name, "blades": rec["blades"], "feasible": rec["feasible"],
           "hoverWatts": h["electrical"], "hoverRpm": h["rpm"], "hoverThrottle": h["throttle"],
           "gramsPerWatt": h["gramsPerWatt"], "figureOfMerit": h["figureOfMerit"],
           "fullThrust": f["thrust"], "fullRpm": f["rpm"], "fullCurrent": f["current"], "tipMach": f["tipMach"],
           "rootSF": f["structure"]["safetyFactor"], "rootStress": f["structure"]["rootStress"], "tipTwistHover": h["structure"]["tipTwist_deg"],
           "tipTwistFull": f["structure"]["tipTwist_deg"], "flapHz": h["structure"]["flapHz"],
           "lagHz": h["structure"]["lagHz"], "frequencyMargin": h["structure"]["frequencyMargin"],
           "responseMs": h["responseTime_ms"], "bladeMass": rec["blades"] * h["structure"]["bladeMass_g"],
           "polars": h["performance"]["polars"], "blade": rec["blade"].to_dict()}
    if extra:
        out.update(extra)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    motor, pack = kit()
    t_hover = spec.all_up_mass() * spec.G / 4
    t_full = spec.required_full_thrust()
    rows = []

    def log(s):
        print(s, flush=True)

    # open rotors
    for name, r_tip in (("open-89", spec.PROP["diameter"] / 2), ("open-100", 50.0)):
        res = pr.design(motor, pack, t_hover, t_full, r_tip, R_HUB, blades=(2, 3, 4), material=MATERIAL,
                        t_min=T_MIN, log=lambda s, n=name: log(f"{n}: {s}"), maxiter=30,
                        hub_height=HUB_H)
        for rec in res["designs"]:
            rows.append(summarise(name, rec))

    # ducted: the blade carries the rotor's share at the duct's exit area ratio; the duct's losses
    # (lip, wall, tip leak) are pressure the rotor makes up, charged as extra shaft power
    r_tip = spec.PROP["diameter"] / 2
    d = duct_for(r_tip, t_hover)
    share = d["rotorThrust"] / t_hover
    loss = sum(d["losses"].values())
    duct = {"exitAreaRatio": d["exitAreaRatio"]}
    res = pr.design(motor, pack, share * t_hover, share * t_full, r_tip, R_HUB, blades=(2, 3, 4),
                    material=MATERIAL, t_min=T_MIN, duct=duct, log=lambda s: log(f"ducted-89: {s}"), maxiter=30,
                    hub_height=HUB_H)
    for rec in res["designs"]:
        e = rec["evaluation"]
        # losses are total pressure the rotor must add: (1 + loss) times the induced share of the shaft power
        ind = d["power"] * (rec["evaluation"]["hover"]["thrust"] / max(d["rotorThrust"], 1e-9)) ** 1.5
        extra_w = loss * min(ind, e["hover"]["shaft"]) / max(e["hover"]["efficiency"], 1e-6)
        row = summarise("ducted-89", rec, {"ductLossWatts": extra_w, "rotorShare": share, "duct": d})
        row["hoverWattsBlade"] = row["hoverWatts"]
        row["hoverWatts"] = row["hoverWatts"] + extra_w
        row["gramsPerWatt"] = t_hover / spec.G * 1000 / row["hoverWatts"]
        row["fullThrust"] = row["fullThrust"] / share
        rows.append(row)

    report = {"hoverThrust": t_hover, "requiredFullThrust": t_full, "motor": spec.MOTOR, "battery": spec.BATTERY,
              "material": MATERIAL, "tMin": T_MIN, "designs": rows}
    (OUT / "props.json").write_text(json.dumps(report, indent=1, default=float))
    finish(report)


def finish(report):
    """The best design of each kind: its root fillet, printable rotors in both hands, and the printed solid
    checked under spin and air loads. `python props.py --finish` redoes this from out/props/props.json."""
    rows, t_hover = report["designs"], report["hoverThrust"]

    def log(s):
        print(s, flush=True)

    feasible = [r for r in rows if r["feasible"]] or rows
    best = {}
    for r in feasible:
        if r["name"] not in best or r["hoverWatts"] < best[r["name"]]["hoverWatts"]:
            best[r["name"]] = r
    report["best"] = {k: v["blades"] for k, v in best.items()}
    motor, pack = kit()
    for k, r in best.items():
        bl = pr.Blade.from_dict(r["blade"])
        # the root fillet from the full-throttle root stress, then the printed solid checked under spin and air loads
        fl = pr.root_fillet(bl, r["rootStress"], 50.0, 2.0, T_MIN)
        # no larger than the hub holds: a fillet that runs off the hub's face is cut there, not carried
        room = max(T_MIN, 0.5 * (HUB_H - pr.hub_height(bl, 0.0, 0.5 * T_MIN)))
        if fl["radius"] > room:
            fl = dict(fl, radius=room, cappedByHub=True)
        r["fillet"] = fl
        for hand in ("ccw", "cw"):
            m = pr.rotor_mesh(bl, bore=5.0, rotation=hand, fillet=fl["radius"], wall=0.5 * T_MIN,
                             height=max(HUB_H, pr.hub_height(bl, fl["radius"], 0.5 * T_MIN)))
            m.export(OUT / f"{k}-{hand}.stl")
            r["hubHeight"] = m.metadata["hubHeight"]
        if k == min(best, key=lambda q: best[q]["hoverWatts"]) or "--check-all" in sys.argv:
            ev = pr.evaluate(bl, motor, pack, (r.get("rotorShare") or 1.0) * t_hover, MATERIAL,
                             duct={"exitAreaRatio": r["duct"]["exitAreaRatio"]} if "duct" in r else None)
            r["solid"] = pr.solid_check(bl, ev["full"]["performance"], MATERIAL,
                                        mesh=pr.rotor_mesh(bl, bore=5.0, fillet=fl["radius"], wall=0.5 * T_MIN,
                                                          height=max(HUB_H, pr.hub_height(bl, fl["radius"], 0.5 * T_MIN))),
                                        size=0.5)
            log(f"{k}: solid check {r['solid']}")
    (OUT / "props.json").write_text(json.dumps(report, indent=1, default=float))
    for k, r in sorted(best.items(), key=lambda kv: kv[1]["hoverWatts"]):
        log(f"{k}: {r['blades']} blades, hover {r['hoverWatts']:.2f} W ({r['gramsPerWatt']:.2f} g/W), "
            f"full {r['fullThrust']:.2f} N, SF {r['rootSF']:.1f}, twist {r['tipTwistHover']:.1f}/{r['tipTwistFull']:.1f} deg, "
            f"{r['bladeMass']:.2f} g of blades, response {r['responseMs']:.1f} ms")


if __name__ == "__main__":
    if "--finish" in sys.argv:
        finish(json.loads((OUT / "props.json").read_text()))
    else:
        main()
