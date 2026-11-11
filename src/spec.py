"""
hum: a 3.5-inch ducted camera quad (cinewhoop class), every structural part
printed and designed with loadpath, everything else off the shelf.

This file is the drone's physics: the off-the-shelf parts (generic classes,
datasheet-typical numbers), where they sit, and every load, frequency, heat
and crash number the printed parts are designed from, each derived here
from momentum theory, rigid-body dynamics and energy, not picked.

Units: mm, kg, N, s, W, Hz unless a name says otherwise.
Run `python spec.py` to print the derived numbers and write spec.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

G = 9.81
RHO_AIR = 1.20            # kg/m^3, 20 C sea level
NU_AIR = 1.5e-5           # m^2/s
K_AIR = 0.026             # W/m K
PR_AIR = 0.71

# --- off-the-shelf parts (generic classes) -------------------------------
MOTOR = {  # 1804-class outrunner, 2450 KV, on 4S
    "kv": 2450, "mass": 0.020, "bellDiameter": 23.0, "height": 15.5,
    "rm": 0.12, "i0": 0.6, "maxCurrent": 25.0,   # winding ohms, no-load amps (datasheet-typical for the class)
    "rotorInertia": 1.0e-6,                       # kg m^2: ~9 g bell at ~10.5 mm
    "boltPattern": 12.0, "bolt": "M2", "boltDepth": 2.5,  # tapped base, screws from below
    "shaftClearance": 6.0,  # circlip/shaft boss under the base
}
PROP = {"diameter": 88.9, "blades": 3, "mass": 0.0035, "hubHeight": 6.0}  # 3.5 in tri-blade
BATTERY = {"cells": 4, "capacity": 0.85, "mass": 0.100, "size": [60.0, 31.0, 30.0], "maxTemp": 60.0,  # 4S 850 mAh LiPo
           "cellVolts": 3.8, "cellOhms": 0.012}                                 # under load; internal resistance
FC = {"mass": 0.006, "board": [27.0, 27.0, 5.0], "pattern": 20.0, "bolt": "M2", "watts": 0.6, "maxTemp": 85.0}
ESC = {"mass": 0.009, "board": [27.0, 27.0, 6.0], "pattern": 20.0, "bolt": "M2",  # 4-in-1, 35 A class
       "wattsHover": 1.2, "wattsFull": 7.0, "maxTemp": 100.0}
VTX = {"mass": 0.018, "board": [33.0, 33.0, 10.0], "pattern": 25.5, "bolt": "M2", "watts": 4.5,  # digital VTX
       "maxTemp": 85.0}
CAMERA = {"mass": 0.008, "body": [19.0, 19.0, 26.0], "lens": 14.0, "watts": 1.0, "maxTemp": 70.0,
          "sideBolts": "M2"}  # 19 mm 'micro' FPV camera, held by two side screws
RX = {"mass": 0.001, "board": [12.0, 10.0, 3.0]}
WIRING = {"mass": 0.020}          # XT30 lead, motor and camera wires, strap, screws
VOLTAGE = 15.2                    # 4S under load

# --- layout ----------------------------------------------------------------
ARM = 52.0                        # motor centres at (+-ARM, +-ARM): 147 mm diagonal wheelbase
TIP_GAP = 1.0                     # prop tip to duct wall (mm)
DUCT_ID = PROP["diameter"] + 2 * TIP_GAP
DUCT_WALL = 0.8                   # the drawn duct skin: SLS PA12's 0.8 mm floor (Materialize); the frame design
                                  # thickens it where the loads need (frame.py: design band outside it)
MOTOR_BASE_Z = 0.0                # the motor seats on z = 0, shaft up, prop above
PROP_Z = MOTOR_BASE_Z + MOTOR["height"] + 2.0   # prop plane
DUCT_Z = (1.5, 24.0)              # duct: 6.5 mm (7% of D) of inlet above the prop plane
FRAME_MASS_BUDGET = 0.060         # printed frame + ducts, first guess (refined by the design)

# --- what it must lift ---------------------------------------------------------
# The mission sets full-throttle thrust, not a habit: carrying PAYLOAD (what the gripper will pick up), it must still
# hold its height banked to BANK_MAX, which is also the authority left to hold attitude in a gust. Thrust per rotor
# at full throttle >= (all-up + payload) g / (4 cos BANK_MAX).
PAYLOAD = 0.100                   # kg
BANK_MAX = 60.0                   # deg

# --- crash rating ------------------------------------------------------------
# 2 m tumbles and 4 m/s wall hits read SF 0.2-0.8 even on a 164 g frame (bumper and frame flexing
# together, loadpath impact cases): designed instead for 1 m and 3 m/s, what cinewhoops survive;
# harder hits may crack a duct, a replaceable print.
WALL_SPEED = 3.0                  # m/s
DROP_HEIGHT = 1.0                 # m

# --- materials (the frame) -------------------------------------------------
FRAME_PROCESS = "sls"
FRAME_MATERIAL = "pa12"           # loadpath card; Materialize PA12 SLS


def all_up_mass(frame=FRAME_MASS_BUDGET):
    return (4 * (MOTOR["mass"] + PROP["mass"]) + BATTERY["mass"] + FC["mass"] + ESC["mass"] + VTX["mass"]
            + CAMERA["mass"] + RX["mass"] + WIRING["mass"] + frame)


def required_full_thrust(frame=FRAME_MASS_BUDGET):
    """Per rotor (N): hold height at BANK_MAX carrying PAYLOAD."""
    return (all_up_mass(frame) + PAYLOAD) * G / (4 * math.cos(math.radians(BANK_MAX)))


def disk_area():
    return math.pi * (PROP["diameter"] / 2000.0) ** 2           # m^2


def max_thrust():
    """Static thrust per motor at full throttle (N). 1804 / 2450 KV / 3.5 in
    tri-blade on 4S test-stand data sits at 560-650 gf; take 610 gf."""
    return 0.610 * G


def induced_velocity(thrust):
    """Momentum theory, hover: v_i = sqrt(T / (2 rho A)) at the disk (m/s);
    the fully developed wake is 2 v_i."""
    return math.sqrt(thrust / (2 * RHO_AIR * disk_area()))


def rpm_at(thrust):
    """Thrust goes as rpm^2. Full throttle loaded rpm: 80% of KV x volts."""
    full = 0.80 * MOTOR["kv"] * VOLTAGE
    return full * math.sqrt(thrust / max_thrust())


def shaft_torque(thrust, figure_of_merit=0.55):
    """Prop drag torque (N m): ideal power T^1.5 / sqrt(2 rho A) over the
    figure of merit, at the rpm that thrust needs."""
    p = thrust ** 1.5 / math.sqrt(2 * RHO_AIR * disk_area()) / figure_of_merit
    return p / (rpm_at(thrust) * 2 * math.pi / 60.0), p


def flat_plate_h(speed, length_mm):
    """Forced convection off a plate in a stream (W/m^2 K), mean over its
    length: laminar Nu = 0.664 Re^0.5 Pr^1/3, turbulent past Re 5e5."""
    re = speed * length_mm * 1e-3 / NU_AIR
    nu = 0.664 * re ** 0.5 * PR_AIR ** (1 / 3) if re < 5e5 else 0.037 * re ** 0.8 * PR_AIR ** (1 / 3)
    return nu * K_AIR / (length_mm * 1e-3), re


def crash(speed, stroke_mm, efficiency=0.8, mass=None):
    """A crash at `speed` (m/s) stopped by a crush bumper over `stroke_mm`
    at `efficiency` (energy / (peak force x stroke), 0.8-0.95 for a graded
    lattice, 0.5 for a linear spring): the peak force (N)."""
    m = mass or all_up_mass()
    e = 0.5 * m * speed ** 2
    return e / (efficiency * stroke_mm * 1e-3), e


def derived():
    m = all_up_mass()
    hover = m * G / 4
    tmax = max_thrust()
    q_hover, p_hover = shaft_torque(hover)
    q_full, p_full = shaft_torque(tmax)
    f_hover = rpm_at(hover) / 60
    f_full = rpm_at(tmax) / 60
    h_fwd, re_fwd = flat_plate_h(8.0, 60.0)   # 8 m/s cruise over a 60 mm canopy
    v_hover = induced_velocity(hover)
    wall_f, wall_e = crash(WALL_SPEED, 8.0)   # into a wall, 8 mm bumper stroke
    drop_h = DROP_HEIGHT
    drop_v = math.sqrt(2 * G * drop_h)
    drop_f, drop_e = crash(drop_v, 8.0)
    return {
        "allUpMass": round(m, 4),
        "frameBudget": FRAME_MASS_BUDGET,
        "hoverThrustPerMotor": round(hover, 3),
        "maxThrustPerMotor": round(tmax, 3),
        "thrustToWeight": round(4 * tmax / (m * G), 2),
        "requiredFullThrustPerMotor": round(required_full_thrust(), 3),
        "hoverRpm": round(rpm_at(hover)), "fullRpm": round(rpm_at(tmax)),
        "rotorHz": [round(f_hover, 1), round(f_full, 1)],
        "bladePassHz": [round(f_hover * PROP["blades"], 1), round(f_full * PROP["blades"], 1)],
        "motorTorqueNm": [round(q_hover, 4), round(q_full, 4)],
        "shaftPowerW": [round(p_hover, 1), round(p_full, 1)],
        "inducedVelocity": [round(v_hover, 2), round(induced_velocity(tmax), 2)],
        "wakeVelocity": [round(2 * v_hover, 2), round(2 * induced_velocity(tmax), 2)],
        "maxVerticalAccelG": round(4 * tmax / (m * G) - 1, 2),
        "cruiseH": round(h_fwd, 1), "cruiseRe": round(re_fwd),
        "wallCrash": {"speed": WALL_SPEED, "energyJ": round(wall_e, 2), "stroke": 8.0, "peakForce": round(wall_f, 1),
                      "peakG": round(wall_f / (m * G), 1)},
        "drop": {"height": drop_h, "speed": round(drop_v, 2), "energyJ": round(drop_e, 2), "stroke": 8.0,
                 "peakForce": round(drop_f, 1), "peakG": round(drop_f / (m * G), 1)},
        "minFrequency": round(1.1 * f_full, 0),
    }


if __name__ == "__main__":
    d = derived()
    print(json.dumps(d, indent=1))
    Path(__file__).with_name("spec.json").write_text(json.dumps(d, indent=1) + "\n")
