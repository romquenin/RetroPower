# Wii

Status: **working**, from Home Assistant and from the console's own power
button.

Build: **bare ESP-12F + PhotoMOS AQY210EH**, no relay. See
[soft-power-buttons.md](../soft-power-buttons.md). Firmware:
[`retropower_wii.yaml`](../../firmware/retropower_wii.yaml).

This was the hardest console of the project. Three traps, each described
below: an always-on rail that cannot carry the ESP, a test point that
switches the console off but never on, and a power button whose ground side
does not look like a ground.

## The points actually used

| Role | Point | Goes to |
|---|---|---|
| Module supply | **12 V input** (`Vin+`) through a buck set to **3.3 V** — TP204 also works | the module's `VCC` |
| Ground | a `GND` pad | the module's `GND`, PhotoMOS pin 2 |
| Sense | the pad silkscreened **`3.3V`** — a 3.3 V pin of a GameCube controller port also works | **GPIO14** |
| Power button, ground side | **TP112** (0 V) | PhotoMOS pin 4 |
| Power button line | the button's **other pad** (~3.3 V, pulled up) | PhotoMOS pin 3 |

All on **side A** of the board.

## Power: TP204, not TP110

**TP110** (next to TP116) also stays at 3.3 V in every state, so it looks
like the obvious choice. It is not: with the ESP on it, the console lost its
**video output** and the ESP did not start. That rail cannot supply an extra
60 mA.

**TP204** carries the module without trouble.

The module was later moved to the **12 V input** (`Vin+` / `Vin-`, top left
of side A) through a small buck set to 3.3 V, while chasing the USB-disk
crash described below. That takes it off the Wii's internal regulators
completely, and it stayed there.

As always on this project: measure a candidate rail **with the ESP connected
and running**, not just with a multimeter on an idle pad.

## Sense: the `3.3V` pad

The Wii has a few voltage test pads with the voltage **printed on the
board**: `5V`, `1V`, `1.15V`, `3.3V` and several `GND`. The one marked
**`3.3V`** sits on the left third of side A, just above **R113**, with a pad
marked `GND` right above it, next to **TP197** and **C247**.

It is the main 3.3 V rail: **0 V in standby, 3.3 V running**. Straight into
GPIO14, no divider.

### Red LED, orange LED

From the Wii manual:

| LED | Meaning |
|---|---|
| Green | console on |
| Orange | standby, **WiiConnect24 on** |
| Red | standby, WiiConnect24 off |

With WiiConnect24 on, part of the console stays awake in standby. Check the
sense in **both** standby modes. The simplest is to switch WiiConnect24 off
in the Wii settings: the service was shut down by Nintendo in 2013 anyway.

## The power button: wire the PhotoMOS across the button, not to ground

This is the trap that cost an evening.

The Wii's button is an ordinary one — pressing it pulls a line low — but
its **ground side is not the board ground you would pick**:

| Pad | In standby |
|---|---|
| **TP112**, the button's ground side | **~0 V** |
| the button's **other pad**, the line, pulled up | **~3.3 V** |

On the physical button (3 pins), the middle pin is ground and both outer
pins sit around 3.3–3.8 V: one is the line (touching it to ground with a
multimeter in continuity mode wakes the console), the other is a stiff
supply that the meter cannot pull down.

What made it confusing:

- **TP112 looked like the line.** It was found first, and the first wiring
  put the PhotoMOS between TP112 and the console ground. That joins ground
  to ground: nothing could happen, while the PhotoMOS's LED side measured
  perfectly.
- **The button's return does not beep with ground** in continuity mode,
  so it looks isolated. Measure the pads in **volts** instead.
- **The multimeter's continuity mode is not a plain wire**: it injects a
  small current out of the red probe, so "it powers on when I touch these
  two pads" does not prove that a plain short does the same. Check with a
  plain wire, or swap the probes.

The fix: PhotoMOS pins 3 and 4 **across the two button pads**, TP112 and
the line pad, exactly like the button itself. The output is a floating
contact, so polarity does not matter.

**When moving a wire from ground to the other pad, remove the ground
connection completely.** Both at once shorts the pulled-up line to ground.

The general rule, valid on every console: put the PhotoMOS **across the
two contacts of the button**, never "from the line to the nearest ground".

## USB disk: power-on crash from standby

With a USB disk plugged in, the Wii sometimes crashed when switched back on
from standby: green LED, then everything off — LED dark, not red — until the
mains was unplugged. The first power-on after the mains always worked; the
problem appeared only on the next power-on from standby. Nothing in the
RetroPower install was to blame (sense moved, button wires filtered, module
moved to 12 V: no change).

The fix is to keep the Wii **disconnected from the disk while it is off**:
that is what the [Wi-Fi USB disk switch](../../projects/usb-switch-wifi/README.md)
does, sharing the disk with the Wii U and handing it to the Wii only while
the Wii is on.

## Do not use TP117

TP117 is on the **processor side** of the button. Touching it with nothing
more than a multimeter probe in volts mode switches a running console off,
but it can never switch it on.

That matches WiiBrew's description of the Hollywood GPIOs: the power button
reaches the processor through a pulse-shaping circuit (`POWER`: "pulse width
limited; will not detect a held-down state"), and the processor then turns
the system off through a `SHUTDOWN` output. In standby, the processor is not
powered, so nothing is listening on that line. Waking the console is done by
a separate standby circuit, directly on the button — hence TP112.

It is also a warning about how sensitive these lines are: keep the button
wires short and twisted together.

## Bare module

An ESP-12F desoldered from a LoLin V3 / NodeMCU board, exactly as on the
[Wii U](wii-u.md): no `D0`–`D8` labels, the pads carry the GPIO numbers.
GPIO4 for the PhotoMOS, GPIO14 for the sense, plus the boot resistors
(`EN` → 10 kΩ → 3.3 V and `GPIO15` → 10 kΩ → GND are mandatory) and 100 nF
across VCC/GND. Flash and validate OTA before desoldering.

## Worth checking after the install

- **Power-on from a Wii Remote**, if the module is on an internal rail
  (TP204): the Bluetooth module lives on a standby rail too. If a Wii
  Remote no longer wakes the console once the ESP is connected, the ESP is
  drawing too much from a shared rail. On the 12 V input + buck, this does
  not apply.
- **The sense with the orange LED**, if WiiConnect24 stays on.

Sources: Shank's Wii Super Thread, on
[BitBuilt](https://bitbuilt.net/forums/threads/shanks-wii-super-thread.66/)
and [ModRetro](https://forums.modretro.com/threads/shanks-wii-super-thread.14659/);
[Hollywood/GPIOs — WiiBrew](https://wiibrew.org/wiki/Special:MobileDiff/88082);
the Wii operation manual for the LED colours.
