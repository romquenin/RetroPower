# Master System

Status: **working**, same procedure as the other consoles with a real power
switch. Integrated board.

## Replacing the ESP32-C3-Zero with a D1 mini

This console's board ended up with a D1 mini instead of the ESP32-C3-Zero,
after the original module turned out to come from a **bad batch with a badly
isolated antenna** — constant Wi-Fi drop-outs. Not a fault of the C3-Zero
itself: the Waveshare modules used on the other consoles are fine.

The swap is worth documenting because it works on an already-assembled
board, without touching anything else.

**The D1 mini does not fit the footprint.** The integrated board's pad
layout is made for the C3-Zero, two rows 15.24 mm apart; the D1 mini's rows
are 22.86 mm apart. It is five flying wires, not a drop-in.

**Only five pads on the module footprint are connected**; the rest are in
the air. Identify them by continuity rather than by counting:

| Signal | Sounds with | D1 mini pin |
|---|---|---|
| 3V3 | K1 pins 1 and 2 | `3V3` |
| GND | J2 pad 2 | `G` |
| SENSE | J6 pad 1 | **D5** (GPIO14) |
| SET | one leg of R1 (the 100 Ω next to Q1) | **D1** (GPIO5) |
| RESET | one leg of R2 (the 100 Ω next to Q2) | **D2** (GPIO4) |

**The pin numbers change, the labels lie.** On the ESP32-C3-Zero the pins
are named by their GPIO number (GP0, GP3, GP10). On a D1 mini, `D0`–`D8` are
silkscreen labels with no relation to the GPIO numbers: D5 is GPIO14, D1 is
GPIO5, D2 is GPIO4. There is no `D5 = D0` equivalence — only the **role**
maps across.

The C3's GPIO numbers cannot simply be reused either: on an ESP8266, GPIO0
is a boot strapping pin, GPIO3 is the serial RX, and GPIO10 is not brought
out on a D1 mini. Hence the three pins above, which have no boot
constraints.

In the firmware, `board: esp32-c3-devkitm-1` becomes `board: d1_mini`, the
platform block becomes `esp8266:`, and the three pin numbers change. Nothing
else moves.
