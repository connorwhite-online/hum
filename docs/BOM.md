# Bill of materials

Every structural part is printed. Everything else is a standard off-the-shelf part. Any part
of the stated class fits: the frame is designed around the class's bolt patterns and envelopes
(`src/spec.py`), not around one brand. Prices are typical 2026 street prices in USD.

## Printed

| Part | Process, material | Qty | File | Notes |
|---|---|---|---|---|
| Frame | SLS PA12 | 1 | `parts/frame.stl` | ducts, arms, motor mounts, stack floor in one piece |
| Bumper | FDM TPU 95A | 4 | `parts/bumper.stl` | graded gyroid crush tyre, 0.45 mm lines, 7 mm cells |
| Canopy | SLS PA12 | 1 | `parts/canopy.stl` | battery, VTX and camera mount (in design) |

## Electronics

| Part | Class (what fits) | Qty | Mass | Typical price |
|---|---|---|---|---|
| Motor | 1804 outrunner, 2400-2500 KV, 12N14P, 12 mm M2 base pattern, 1.5 mm shaft | 4 | 20 g | $16 |
| Propeller | 3.5 in tri-blade, 1.5 mm shaft, for ducts (low tip loading) | 4 (+spares) | 3.5 g | $1 |
| Flight controller | 20x20 M2, Betaflight 4.5+, ICM-42688 class gyro, 4 UARTs | 1 | 6 g | $40 |
| ESC | 20x20 M2 4-in-1, 35 A class, 2-6S, BLHeli_32/AM32 (bidirectional DShot) | 1 | 9 g | $45 |
| Video transmitter | Digital HD VTX, 25.5x25.5 M2, about 4.5 W | 1 | 18 g | $80-170 |
| Camera | 19 mm "micro" FPV camera, side M2 mounts | 1 | 8 g | (usually with the VTX) |
| Receiver | ELRS 2.4 GHz nano, UART | 1 | 1 g | $15 |
| Battery | 4S 850 mAh LiPo, 75C+, XT30, at most 60x31x30 mm, about 100 g | 2+ | 100 g | $20 |

## Hardware

| Part | Qty | Where |
|---|---|---|
| M2 x 6 socket head, steel | 16 | motors to frame (3 mm grip into the motor's 2.5 mm thread) |
| M2 x 20 socket head | 4 | flight stack, through soft-mount grommets |
| M2 heat-set insert, 3 mm long | 8 | 4 under the stack, 4 in the canopy posts |
| M2 x 6 button head | 4 | canopy to posts |
| M2 nylon nut | 4 | stack top |
| Silicone grommets, M2, 20x20 stack | 4 | come with most FC/ESC |
| Battery strap, 10 x 150 mm, rubberized | 1 | battery to canopy |
| Anti-slip battery pad | 1 | under the battery |
| XT30 pigtail, 12 AWG, 60 mm | 1 | (usually with the ESC) |
| Low-ESR capacitor, 35 V 470 uF | 1 | across ESC power pads |
| Zip ties, 2.5 mm | 8 | motor wires along the arms |
| Heat-shrink, 3 mm and 10 mm | - | |

## Custom PCB

None. The 4-in-1 ESC already distributes battery power to the motors, and the flight
controller's regulated pads (5 V, 10 V) power the receiver, camera and VTX. A custom board would
add mass and a failure point without carrying a load or a signal the stack does not already
carry. If a later version adds lights or a buzzer the stack has no pads for, a board earns its
place then.
