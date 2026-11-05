# Wii

Status: **working**, from Home Assistant and from the console's own power
button.

Build: **bare ESP-12F + PhotoMOS AQY210EH**, no relay. See
[soft-power-buttons.md](../soft-power-buttons.md). Firmware:
[`retropower_wii.yaml`](../../firmware/retropower_wii.yaml).

This was the hardest console of the project. Three traps, each described
below: an always-on rail that cannot carry the ESP, a test point that
switches the console off but never on, and a power button that works the
other way round from every other console.

## The points actually used

| Role | Point | Goes to |
|---|---|---|
| Always-on 3.3 V | **TP204** | the module's `VCC` |
| Ground | a `GND` pad | the module's `GND`, PhotoMOS pin 2 |
| Sense | the pad silkscreened **`3.3V`** | **GPIO14** |
| Power button line | **TP112** | PhotoMOS pin 4 |
| Power button, other side | the button's **other pad** (3.3 V standby) | PhotoMOS pin 3 |

All on **side A** of the board.

## Power: TP204, not TP110

**TP110** (next to TP116) also stays at 3.3 V in every state, so it looks
like the obvious choice. It is not: with the ESP on it, the console lost its
**video output** and the ESP did not start. That rail cannot supply an extra
60 mA.

**TP204** carries the module without trouble.

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

## The power button is active high

This is the trap that cost an evening.

On every other console in this project, the power button pulls a line to
ground. **On the Wii it does the opposite**:

| Pad | In standby |
|---|---|
| **TP112**, the button line | **~0 V** |
| the button's **other pad** | **~3.3 V** standby |

Pressing the button brings 3.3 V onto TP112. Pulling TP112 to ground does
nothing, since it is already there.

What made it confusing:

- **The other pad looks like an isolated ground.** It does not beep with
  ground in continuity mode, which is true — because it is a supply, not a
  ground. Measure it in **volts**.
- **The multimeter's continuity mode is not a plain wire.** It injects a
  small current out of the **red** probe. Red on TP112 and black on ground
  powers the console on, so it looks like "TP112 to ground works". It is
  actually the red probe's positive voltage doing it. Swap the probes and
  nothing happens. The PhotoMOS, like a real wire, only connects — so wired
  between TP112 and ground it did nothing at all, while its LED side
  measured perfectly.

The fix: PhotoMOS pins 3 and 4 **across the two button pads**, TP112 and
the 3.3 V pad, exactly like the button itself. The PhotoMOS output is a
floating contact, so this is safe and polarity does not matter.

**When moving the wire from ground to the 3.3 V pad, remove the ground
connection completely.** Both at once is a dead short between the 3.3 V
standby rail and ground.

This is also, in hindsight, the strongest argument for the PhotoMOS over a
MOSFET: a MOSFET can only pull a line to ground, so it could not have driven
this button at all.

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

- **Power-on from a Wii Remote.** The Bluetooth module lives on a standby
  rail too. If a Wii Remote no longer wakes the console once the ESP is
  connected, the ESP is drawing too much from a shared rail.
- **The sense with the orange LED**, if WiiConnect24 stays on.

Sources: Shank's Wii Super Thread, on
[BitBuilt](https://bitbuilt.net/forums/threads/shanks-wii-super-thread.66/)
and [ModRetro](https://forums.modretro.com/threads/shanks-wii-super-thread.14659/);
[Hollywood/GPIOs — WiiBrew](https://wiibrew.org/wiki/Special:MobileDiff/88082);
the Wii operation manual for the LED colours.
