"""
hum firmware: a Betaflight CLI diff, written from the drone's physics.

Any 20x20 Betaflight flight controller of the class in spec.FC runs it: flash
the board's stock Betaflight target (4.5 or later), then paste
firmware/betaflight.txt into the CLI. Only what the drone's physics decides is
set here; the board's pin map (resources) stays the target's own.

What is derived, and from what:
- the RPM filter: motor poles (12N14P stator), bidirectional DShot, and which
  rotor harmonics a three-blade prop excites (1x from imbalance, 3x from blade
  pass, 2x weak);
- the dynamic notch: placed on the frame's first free-free mode, from the
  frame's own modal check (studies/frame report) or the spec floor;
- the gyro lowpass: kept below hover blade pass, above the control band;
- hover throttle (thr_mid): static thrust goes as throttle squared, so hover
  sits at sqrt(hover / max thrust);
- battery limits: 4S LiPo, 850 mAh.
PIDs are left at Betaflight's defaults: they need a measured step response
(blackbox), not a model, and the build guide says how to take one.

Run `python firmware.py` (after spec.py) to write firmware/betaflight.txt.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MOTOR_POLES = 14          # 1804 outrunner: 12 slots, 14 magnets
BLADES = 3


def frame_first_mode():
    """The frame's first flexible free-free mode (Hz): the frame report if the
    frame has been designed and checked, else the spec's floor."""
    for p in (ROOT / "studies" / "frame" / "report.json", ROOT / "parts" / "frame-report.json"):
        if p.exists():
            r = json.loads(p.read_text())
            modal = (r.get("verify") or r).get("modal") or {}
            f = (modal.get("frequencies") or [None])[0]
            if f:
                return float(f), str(p.relative_to(ROOT))
    spec = json.loads((HERE / "spec.json").read_text())
    return float(spec["minFrequency"]), "spec floor (frame not checked yet)"


def settings():
    spec = json.loads((HERE / "spec.json").read_text())
    rotor_lo, rotor_hi = spec["rotorHz"]
    bpf_lo, _ = spec["bladePassHz"]
    f1, f1_from = frame_first_mode()
    hover = spec["hoverThrustPerMotor"] / spec["maxThrustPerMotor"]
    thr_mid = round(100 * math.sqrt(hover))
    out = [
        ("# motors: bidirectional DShot gives the RPM filter each motor's speed", None),
        ("motor_pwm_protocol", "DSHOT600"),
        ("dshot_bidir", "ON"),
        ("motor_poles", MOTOR_POLES),
        (f"# RPM filter: three-blade props excite 1x (imbalance) and {BLADES}x (blade pass); 2x is weak", None),
        ("rpm_filter_harmonics", BLADES),
        ("rpm_filter_weights", "100,0,100"),
        (f"# lowest notch at 60% of hover rotor speed ({rotor_lo:.0f} Hz): idle and descents", None),
        ("rpm_filter_min_hz", int(round(0.6 * rotor_lo))),
        (f"# dynamic notch on the frame's first free-free mode, {f1:.0f} Hz ({f1_from})", None),
        ("dyn_notch_count", 1),
        ("dyn_notch_q", 500),
        ("dyn_notch_min_hz", int(round(0.8 * f1))),
        ("dyn_notch_max_hz", int(round(min(1000, 1.3 * f1)))),
        (f"# gyro lowpass under hover blade pass ({bpf_lo:.0f} Hz), over the control band", None),
        ("gyro_lpf1_dyn_min_hz", int(round(min(250, 0.45 * bpf_lo)))),
        ("gyro_lpf1_dyn_max_hz", int(round(min(500, 0.9 * bpf_lo)))),
        ("# battery: 4S LiPo, 850 mAh", None),
        ("vbat_min_cell_voltage", 330),
        ("vbat_warning_cell_voltage", 350),
        ("bat_capacity", 850),
        ("# props out: the wash leaves the camera's side, and ducts keep blades off the ground", None),
        ("yaw_motors_reversed", "ON"),
        (f"# hover throttle: thrust ~ throttle^2, hover {100 * hover:.0f}% of full thrust", None),
        ("thr_mid", thr_mid),
        ("thr_expo", 30),
    ]
    return out


def write():
    lines = ["# hum: Betaflight CLI diff, written by src/firmware.py from src/spec.json",
             "# paste into the Betaflight CLI on a stock 4.5+ target, then: save", ""]
    for k, v in settings():
        lines.append(k if v is None else f"set {k} = {v}")
    lines += ["", "save", ""]
    (ROOT / "firmware").mkdir(exist_ok=True)
    (ROOT / "firmware" / "betaflight.txt").write_text("\n".join(lines))
    return lines


if __name__ == "__main__":
    print("\n".join(write()))
