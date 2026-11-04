# PlayStation 1 (fat)

Status: **working** (power on and off from Home Assistant, console button
still works). Integrated board, relay version.

## The power switch is on the low-voltage side

This is the point that decides the whole install. On the PS1 fat the front
switch **does not cut the mains**: it disconnects the supply rails from the
motherboard. The power block stays energised as long as the cord is in.

So the relay can be wired straight across it, like on the other consoles
with a real switch.

> **Safety.** That also means the power block keeps mains inside it, and up
> to about 400 V on the primary, even with the console "off". Unplug the
> cord before touching anything, and keep the RetroPower board away from
> the block — both for clearance and because it is a switching supply
> sitting next to a high-impedance sense line.

## Two poles to bridge

The switch has **two poles**: continuity shows two independent pairs, one
carrying 7.5 V and the other 3.5 V. Both have to be bridged, so both relay
contacts are used:

| Connector | Wired to |
|---|---|
| J4 (COM + NO) | the 7.5 V pole of the switch |
| J5 (COM + NO) | the 3.5 V pole |
| J6 | sense, see below |

`NC` (the middle pad) stays unused on both.

The console's own switch must be left on **OFF**: the relay is in parallel
with it, so leaving it ON keeps the console permanently powered and Home
Assistant has nothing left to control.

## Sense

Take `POWER_SENSE` on the **3.5 V rail after the switch**, motherboard side:
0 V with the console off, about 3.3–3.5 V when it runs.

Measured on the 5-pin PSU connector: two grounds, one pin at about 8.2 V
(the 7.5 V rail) and two pins around 3.3 V that are the same net — one
bridging wire is enough.

## Powering the ESP

On this console we powered the ESP32 over **USB**, not from the console:
`J1` pin 1 (3V3) and pin 2 (GND) feed the board *from* the ESP's own 3.3 V
regulator, and `J2`/`J3` are left unwired — no buck converter at all.

The relay coils run on that 3.3 V, so **C1 is not optional** in this
configuration: it supplies the coil pulse that the ESP's regulator cannot
deliver on its own.

## Not related to RetroPower: the USB-C PSU replacement

A separate experiment on the same console, recorded here because it cost a
whole evening: replacing the original power block with a generic AliExpress
USB-C board (Auroxin type, 12 V PD in) produced **constant video noise** on
the RGB output.

What we established:

- Powering the board from a **powerbank** gave a perfectly clean picture.
  So neither the clone board, nor the RGB cable, nor the scaler settings
  were at fault — the noise came in through the mains.
- An **earthed 65 W charger did not fix it**. Measured afterwards: that
  charger's output is not actually bonded to earth, only its internal
  shield is. Worth checking with a continuity test between the USB-C
  shell and the earth pin before buying one for that reason.
- **100 nF on both output rails changed nothing**, which points at a
  common-mode current rather than ripple on the rails.
- A **ground wire from the console to the scaler** reduced the noise
  markedly, confirming a ground loop, but did not remove it entirely.

We put the original power block back. Keep this in mind before converting a
console that feeds an analogue scaler.
