# Wii U

Status: **working**, from Home Assistant and from the console's own power
button. Everything soldered straight to the motherboard test points, first
attempt.

Build: **bare ESP-12F + PhotoMOS AQY210EH**, no relay. See
[soft-power-buttons.md](../soft-power-buttons.md).

## The three points actually used

| Role | Point | Goes to |
|---|---|---|
| Always-on 3.3 V | **TP22** | the module's `VCC` |
| Ground | **TP164** | the module's `GND` |
| Power switch | **TP70** | PhotoMOS pins 3/4, with ground |
| Sense | a round plated pad, see below | **GPIO14** |

WiiUBrew documents **TP122** as the always-on 3.3 V rail and **TP114** as
the drive's always-on 3.3 V. TP22 is what was measured and used here.
Measure your own board rather than trusting either list blindly.

### The sense point

The pad used is the **round plated pad** highlighted in BitBuilt's Wii U
voltage map, inside the 3.3 V zone next to **TP142 / TP161**: C406 sits
above it, C1453 below and to its right, Q1077 and R1300 lower-left. It
carries no `TPxxx` designation on that map. 3.3 V straight into GPIO14, no
divider.

Check the sense in **every** state, connected standby included — the Wii U
stays on the network for downloads and to charge the GamePad, and the point
must fall back to 0 V there.

**Avoid TP139**, the Wi-Fi module's supply: its enable line (TP141) comes
from the RTC, so it can stay alive in standby.

## Bare module

The module is an ESP-12F desoldered from a LoLin / NodeMCU dev board. On a
bare module there are **no `D0`–`D8` silkscreen labels** — the pads carry the
GPIO numbers directly, so there is no translation to do: `GPIO4` for the
PhotoMOS, `GPIO14` for the sense.

Boot resistors, which are what the dev board was providing for you:

| Pad | To | |
|---|---|---|
| `EN` | 10 kΩ → 3.3 V | **mandatory**, the chip stays dead without it |
| `GPIO15` | 10 kΩ → GND | **mandatory** |
| `GPIO0` | 10 kΩ → 3.3 V | recommended |
| `GPIO2` | 10 kΩ → 3.3 V | recommended |
| `RST` | 10 kΩ → 3.3 V | recommended |

100 nF between VCC and GND as close to the module as possible. Add an
electrolytic (100 µF or more) if Uptime keeps resetting itself. The module
draws about 62 mA at 3.3 V, roughly 0.2 W.

**Flash and validate OTA before desoldering the module from its dev board** —
afterwards there is no USB left.

On some older ESP-12 modules the **GPIO4 and GPIO5 silkscreen is swapped**
relative to the actual chip pins. The check is free while the module is
still on its dev board: flash it, trigger the short press from Home
Assistant, and see which pad goes to 3.3 V.

## Where the test points are

Unlike most consoles, the Wii U's test points are **silkscreened on the
board itself** — look for `TPxxx` next to the pads. They are mostly on the
**underside, opposite the SoC**, so a magnifier is enough to find them.

Sources:
[Hardware/Testpoints — WiiUBrew](https://wiiubrew.org/wiki/Hardware/Testpoints),
and BitBuilt's Wii U motherboard voltage map.
