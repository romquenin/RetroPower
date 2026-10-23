# Wi-Fi control for a CSL 41811 Toslink switch

Side project, not part of the RetroPower board: it applies the same idea
(ESP + Home Assistant) to an optical audio switch, so that the Toslink input
follows the console that is running.

Status: **working**, direct selection of each input plus power, from Home
Assistant. Tested on one unit (CSL 3x1 Toslink switch, `Mod.-Nr. 41811`,
PCB marking `901-PCB-V1.0`). The photos and measurements below are from that
unit; another batch may differ, so measure before you solder.

## Idea

The switch has three optical inputs, one output, a button that cycles the
inputs, and a 3.5 mm jack for an external IR eye. The remote has one code per
input, so inputs can be selected directly. Instead of an IR LED, the ESP
drives the **signal line of the IR jack** through a MOSFET, replaying the
remote's codes. No LED, no aiming, and nothing is cut on the switch.

## What is on the board

- Optical input selection: Toshiba **TC74VHC153** (dual 4:1 multiplexer).
- Control: an **STC 8051-family microcontroller** in SOP16 (marking
  `STC… 35I-SOP16G`; probably an STC11F01E, not confirmed). It reads the
  button and the IR jack and drives the multiplexer and the three LEDs.
- Logic around 5 V: with the switch powered from USB, the LED anodes read
  4.80 V with the LED off and 2.79 V (blue LED forward voltage) when lit.

## IR jack (CK1)

A 3.5 mm stereo jack with four solder points, which behave like this on our unit:

| Pad | Jack empty | Eye plugged | Role |
|---|---|---|---|
| Ground pad | continuity with PCB GND | | GND |
| Signal pad | 4.85 V | 3.95 V | **signal** (pulled up by the board, pulled low by the eye) |
| Two other pads | 3.39 V, continuous with each other | 3.30 V | probably the eye supply (inferred; not needed) |

The signal pad is the one that falls from about 4.85 V to about 3.95 V when
the eye is plugged. That the emitter works when wired there confirms it.

## NEC codes

Captured by sniffing the jack while a Logitech Harmony Hub drove the switch.
All codes are NEC with address `0xFF00` (ESPHome representation):

| Function | Command |
|---|---|
| Input 1 | `0xA25D` |
| Input 2 | `0xE11E` |
| Input 3 | `0xE31C` |
| Power (toggle) | `0xE817` |

## Wiring (emitter)

One N-channel MOSFET (AO3400A, SOT-23) pulls the signal line low, as the eye
does when it sees light:

```
                  3 = DRAIN
                      │
                      └──────────► signal pad of the IR jack

              ┌───────┴───────┐
              │    AO3400A    │
              └───┬───────┬───┘

            1 = GATE     2 = SOURCE
                │             │
                │             └──────► GND (switch GND and D1 mini GND)
                │
                ├──[10 kΩ]───────────► GND
                │
           [100 Ω]
                │
                └──────────────────► D2 of the D1 mini (GPIO4)
```

SOT-23 seen from above with the marking up: one pin on top (drain), two at
the bottom (gate left, source right). If you are not sure, identify the pins
with the multimeter in diode mode: the pair that reads about 0.5 to 0.7 V in
one direction only is source (red) and drain (black); the remaining pin is the gate.

- The D1 mini is powered from the switch's own 5 V (USB-C input pads) and its
  GND is common with the switch's GND.
- The 10 kΩ keeps the gate low while the D1 mini boots, so the switch does not
  see stray pulses.

Firmware: [`toslink_switch_wifi.yaml`](toslink_switch_wifi.yaml) (ESPHome,
ESP8266). It exposes four buttons (Input 1, 2, 3, Power) to Home Assistant.
`carrier_duty_percent: 100%` is used because the jack carries the
already-demodulated signal, so there is no 38 kHz carrier to generate.

## Reading the codes (optional)

To capture codes from another remote or hub, add a second MOSFET: gate on the
signal pad through 100 kΩ, source on GND, drain on D5 with `INPUT_PULLUP`
(the signal arrives inverted, so `inverted: false`), then enable the
commented `remote_receiver` block in the YAML.

## Pitfalls we hit

- **Do not wire a GPIO to the signal pad through a plain resistor.** Even 1 kΩ
  loaded the line: the switch stopped reacting to its remote and to the
  Harmony Hub, with or without the ESP powered. Use a MOSFET so the line sees
  only a gate.
- **A suspicious MOSFET shows up on the meter before the circuit does.** A
  re-used MOSFET (desoldered once) read about 10 Ω from gate to GND instead of
  10 kΩ and held the signal line low. Replacing the MOSFET and the
  resistors fixed it. Test a MOSFET on its own (gate to the other pins reads
  open) before putting it in the circuit.
- **Check every step with a voltage reading on the signal pad** (about 3.95 V
  with the eye plugged, switch powered). If it drops, remove the last wire you
  added.
- **Resistor codes on SMD parts:** `1000` = 100 Ω, `1002` = 10 kΩ.
- Some multimeters show a diode drop in millivolts in continuity mode: a
  reading such as 416 or 575 without a beep is a semiconductor junction, not
  ohms.
- **Take the 5 V before the on/off slide switch** (the USB-C pads), or the ESP
  loses power each time the switch is turned off.

## Not covered

- The Home Assistant automation that selects the input from the console
  that is running (for instance a console state sensor driving the Input
  buttons). It uses only the four ESPHome buttons above.
- Fitting everything inside the case.

Provided as-is, no warranty. Measure your own unit before soldering; do not
assume the pads and voltages above match yours.
