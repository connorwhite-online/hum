# What loadpath could not represent (and what we did about it)

The drone is a full-stack test of loadpath. Every place where the library could not model the real
physics is written down here, with what was fixed in loadpath and what is still open.

| # | Gap | Why it matters for the drone | Status |
|---|---|---|---|
| 1 | Inertia relief balanced loads with the part's own (design-space) mass only | Motors, battery and stack are ~80% of the drone's mass; a thrust case pulled on the frame's corners instead of on the battery in its middle (a dumbbell bar read half its bending moment) | **Fixed** in loadpath 3b58223: `inertiaRelief.masses` |
| 2 | Natural frequencies only for a clamped part | A drone in flight is free-free; its first flexible mode is what the props excite | **Fixed** 3b58223: free-free modes for inertia-relief parts, carried masses included |
| 3 | A carried mass could only sit on its mounts | The battery's centre is ~23 mm above its posts: in a crash its inertia twists the posts (m a h), and it rocks on them at a far lower frequency | **Fixed** a0e14d3: `masses[].at` (+ `size` / `inertia`) makes it a rigid body |
| 4 | Cooling had only still air (h = 10 W/m^2K) outside | In flight the canopy sits in an 8 m/s stream: h ~ 51 | **Fixed** e244720: `cooling.skin.airflow` (flat plate + natural + radiation) |
| 5 | One safety factor for every load case | Flight loads want SF 2 plus fatigue; a crash may use most of the strength (SF 1.25) | Open. Worked around: crash forces scaled by 1.25/2 |
| 6 | No aerodynamic cost for structure in a rotor's wake | Arms and spokes under the prop block thrust; the optimizer sees them as free | Open |
| 7 | Vibration is a floor (`minFrequency`) only | The 1x rotor line sweeps 179-497 Hz and blade pass 536-1490 Hz with throttle; a floor above the 1x band is the best available | Open (floor at 1.1 x full-throttle 1x = 546 Hz) |
| 8 | No ducted-propeller thrust model (fan.py is a fan against a system curve) | Duct inlet lip and tip gap set the thrust gain | Open |
| 9 | Cooling airflow is steady; a cycle cannot change it per phase | The worst case is idling on the ground with the VTX on (no flow), then flight cools it | Open |
| 10 | Motor heat softening the PA12 under the motor | Motors run 60-80 C; PA12 loses stiffness well before that | Open (durability at 50 C only) |
| 11 | The impact model crushes flat layers along one axis; a round tyre meets a wall at a point | The cap's first layers are tiny, so even at the softest printable density the force ramps up: the 4 m/s hit reads 499 N against the 395 N the energy alone would allow in 10 mm. A tyre profile shaped for constant layer area (flatter faces) would do better | Open (frame designed for the 499 N the bumper gives) |
| 12 | The impact model takes one material limit per study; SLS TPU's 1.0 mm walls cannot make a gyroid soft enough | Forced FDM TPU 95A (0.45 mm lines, 7 mm cells) for the bumpers | Noted |

