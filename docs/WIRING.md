# Wiring

The flight controller (FC) and the 4-in-1 ESC stack on the frame's 20x20 floor, ESC
at the bottom, so the battery current runs the shortest way and the ESC's heat has the
frame floor and the prop wash below it. Camera, VTX and receiver ride in the canopy.

## Power

| From | To | Wire | Notes |
|---|---|---|---|
| Battery XT30 | ESC BAT+/BAT- pads | 12 AWG, 60 mm | out the back, under the strap |
| ESC BAT pads | 470 uF 35 V capacitor | legs trimmed short | absorbs the motors' voltage spikes |
| ESC | FC | 8-pin JST-SH harness (from the stack) | VBAT, GND, current, telemetry, M1-M4 signal |
| FC 10 V pad | VTX power | 26 AWG pair | VTX at 4.5 W draws about 0.45 A at 10 V |
| FC 5 V pad | Receiver | 30 AWG | |
| FC 5 V or VTX | Camera | (VTX harness) | digital systems feed the camera from the VTX |

## Signal

| From | To | Use |
|---|---|---|
| FC UART1 TX/RX | VTX RX/TX | MSP DisplayPort (OSD) and VTX control |
| FC UART2 TX/RX | Receiver RX/TX | ELRS (CRSF) |
| ESC M1-M4 | Motors | three phase wires each, any order: direction is set in software |

## Motors

Looking down, front at the top. `yaw_motors_reversed = ON` (props out) is set in
`firmware/betaflight.txt`; set each motor's direction in the ESC configurator to match.

| Betaflight motor | Position | Spin (from above) |
|---|---|---|
| M1 | rear right | counter-clockwise |
| M2 | front right | clockwise |
| M3 | rear left | clockwise |
| M4 | front left | counter-clockwise |

Motor leads run inboard along the top of each arm, zip-tied at two points, and are cut to
length at the ESC pad (about 55 mm from the motor base). They stay out of the prop's wake:
the arm under them already sits there.

## Checks before the first battery

1. No continuity between BAT+ and BAT- at the XT30.
2. First power-up through a smoke stopper (a fuse or a current-limited supply).
3. In the Betaflight configurator: motors tab, props off. Each motor spins in its slot and the
   direction above.
