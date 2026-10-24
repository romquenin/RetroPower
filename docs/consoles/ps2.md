# PlayStation 2 (fat)

Status: **working** (power on and power off from Home Assistant). Game reset
works only while no hard drive is connected, see the note below.
Tested on an SCPH-30004R (motherboard GH-015).

Unlike the other consoles in this folder, the PS2 power button is a
**momentary button read by the console's logic**, not a switch that stays
closed. RetroPower therefore does not hold the relay closed: the firmware
simulates a button **press** (relay closed for a moment, then reopened).

| Press on the Power button | Console off | Console on |
|---|---|---|
| Short | Turns on | Resets the game (not with a hard drive connected) |
| Long (about 3 s) | | Turns off |

## Power button ribbon (SCPH-30004R / GH-015)

The Power/Eject buttons and the LEDs are on a front board connected to the
motherboard through a 7-pin ribbon. Pin numbers below count from the **left**
when looking at the white connector with the ribbon facing you, as in our
photo. The numbering is ours, not Sony's: check with a multimeter on your own
board, the pin order may differ between revisions (some GH-015 sub-revisions
are reversed).

| Pin | Measured | Role |
|---|---|---|
| 1 | about 3.5 V | LED return |
| 2 | about 3.5 V (pulled to 0 V when Power is pressed) | **Power switch (PWR_SW)** |
| 3 | 0 V | Ground (second ground, check continuity with pin 4) |
| 4 | 0 V | **Ground** |
| 5 | about 9.8 V | LED line (through a resistor) |
| 6 | about 0.5 V | LED return |
| 7 | 12 V | Common LED supply |

**Never connect pins 1, 5, 6 or 7 to the ESP32**: they carry up to 12 V and
the ESP32 pins tolerate 3.3 V.

J4 goes across **pin 2 and pin 4** (relay contact in parallel with the
button). The contact is dry, polarity does not matter. Pins are very fine:
solder instead on the Power button pads of the front board, after checking
with continuity that one pad goes to pin 2 and the other to pin 4.

## How we found it

1. Console unplugged, multimeter in continuity mode: pin 4 to the chassis
   gives the ground.
2. Console plugged in, standby (red LED): measure each pin to ground.
3. Pressing Power while measuring each of the 3.5 V pins: the line that drops
   to 0 V is the Power switch (pin 2).
4. Diode test between pins 1 and 7 reads about 1.65 V (a red LED forward
   voltage), no beep in continuity mode: LED lines, not buttons.

## Supplies

- **Always-on supply:** the internal PSU of the console outputs 12 V even in
  standby (rear switch on). Tap its output pads for the buck converter, with
  the console unplugged and the capacitors discharged. The PSU is mains
  powered: touch nothing on the primary side. A replacement PSU board is not
  needed if the original works.
- **POWER_SENSE:** use a point at about 3.3 V that is live only while the
  console is on. Measure it in standby first (0 V expected).

## Firmware

Use [`firmware/retropower_ps2.yaml`](../../firmware/retropower_ps2.yaml). It
adds a `press_button` script (SET, hold, RESET), a Reset button entity, a
**Force off** button (a long press that does not look at POWER_SENSE, useful
when the console is stuck or the sense input is wrong; it turns the console
ON if it is really off), and opens the relay contact at boot so that a relay
left closed cannot hold the button pressed. The power-off press length
(`press_off_ms`, 3000 ms) is the value to tune on your console: on ours it
stopped being enough at some point, while the 6 s Force off press always worked.

## Notes

- The firmware presses only if the console is not already in the requested
  state, so POWER_SENSE has to be reliable.
- Do not add a "reset relay at boot" that closes the contact: on this console
  that would press the button.
- **Coil pulses: use 100 ms.** With 30 ms (close to the relay's minimum) a
  RESET pulse was sometimes missed, which leaves the contact closed, i.e. the
  button held down (the console stayed in reset: green LED, no boot, no power
  on the controller ports).
- **Reset does nothing once a hard drive is connected.** On our console the
  Reset button worked during the first tests (console out of its case, no hard
  drive) and stopped working after the hard drive was fitted; presses of 500 ms
  to 2 s from the relay had no effect, while the long power-off press still
  worked. A reply from the owner of the PSBBN Definitive Project says that this
  is by Sony's design: when a hard drive is connected, the reset button is
  disabled to prevent drive corruption
  ([issue #404](https://github.com/CosmicScale/PSBBN-Definitive-Project/issues/404)).
  We have not checked this ourselves beyond the behaviour above. The same
  reply mentions a controller key combination to leave a game when OPL is the
  game launcher; see that project's readme.
