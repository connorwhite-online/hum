# hum

A 3.5-inch ducted camera quadcopter whose every structural part is printed and designed with
[loadpath](https://github.com/connorwhite-online/loadpath). Everything else is off the shelf: motors, props,
flight controller, ESC, video transmitter, camera, battery, screws.

hum is loadpath's full-stack test subject. The drone exercises nearly every part of the library (free-flying
structures, crash and drop, vibration against the rotor frequencies, an electronics enclosure with heat and
airflow, wiring, print DFM), and every place the library could not represent the real physics is logged in
[docs/GAPS.md](docs/GAPS.md) and fixed in loadpath where it can be.

## Spec

| | |
|---|---|
| Class | 3.5 in ducted quad (cinewhoop), 158 mm motor-to-motor diagonal |
| Motors | 4x 1804-class, 2450 KV, 4S; 12 mm M2 pattern |
| Props | 3.5 in (88.9 mm) tri-blade, 1 mm tip gap to the duct |
| Battery | 4S 850 mAh LiPo, 100 g, strapped on top |
| Electronics | 20x20 flight controller + 4-in-1 ESC stack, digital VTX (4.5 W), 19 mm FPV camera, receiver |
| Printed | SLS PA12 frame (ducts, motor mounts, stack floor) and canopy; TPU bumpers |
| All-up mass | ~316 g (frame budget 60 g, refined by the design) |

## Physics the parts are designed from

All numbers come from [`src/spec.py`](src/spec.py) (momentum theory, rigid-body dynamics, energy); none are picked.

| | Value | From |
|---|---|---|
| Hover thrust per motor | 0.78 N | all-up weight / 4 |
| Full thrust per motor | 5.98 N (610 gf) | test-stand class data; thrust-to-weight 7.7 |
| Rotor speed | 10.7k rpm hover, 29.8k full | thrust ~ rpm^2, full at 80% of KV x 15.2 V |
| 1x rotor line | 179-497 Hz | rpm / 60 |
| Blade pass | 536-1490 Hz | 3 blades |
| Motor reaction torque | 9-70 N mm | ideal power / figure of merit 0.55 / shaft speed |
| Prop wake | 14 m/s hover, 40 m/s full | 2 x induced velocity, sqrt(T / 2 rho A) |
| Frame first mode floor | 546 Hz | 1.1 x full-throttle 1x line |
| Wall crash, 3 m/s | 1.42 J, 222 N peak (72 g) | energy into an 8 mm bumper at 0.8 crush efficiency |
| Drop, 1 m | 3.1 J, 484 N peak (156 g) | same bumper |
| Canopy cooling in flight | h = 51 W/m^2K at 8 m/s | flat plate over a 60 mm canopy, plus radiation |

## Layout

- `src/spec.py`: off-the-shelf parts, layout and every derived load.
- `src/frame.py`: the frame study (writes `studies/frame.study.json`).
- `studies/`: loadpath studies.
- `parts/`: delivered STLs.
- `docs/GAPS.md`: what loadpath could not represent, and what was done about it.
