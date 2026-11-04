# Consoles with a soft / touch power button — no relay needed

The relay on the RetroPower board exists because older consoles have a
**real power switch** that carries the supply rails: the contact has to stay
closed, and it has to pass an amp or so.

Consoles from the PS3 generation onwards do not work like that. Their power
button is a **logic input**: a touch pad or a micro-switch whose only job is
to pull one line to ground so the console's management controller sees a
press. That line carries microamps.

For those, the RetroPower PCB is overkill. A single switching device across
the button contacts, driven by one GPIO, does the whole job. Tested on
PS3 fat, Xbox 360 Slim and PS4 Pro.

| | Relay (RetroPower board) | Single device (this page) |
|---|---|---|
| Console | Real power switch | Soft / touch button |
| What it switches | The supply rails, ~1 A | A logic line, µA |
| Keeps state without power | Yes (bistable) | No — but irrelevant, we only pulse |

## Two ways to do it

### PhotoMOS AQY210EH — recommended

A solid-state relay: an LED on the input side, two MOSFETs back to back on
the output side, optically isolated. 350 V / 130 mA, 18–25 Ω on-resistance,
5000 V isolation.

```
GPIO ──[470 Ω]── 1 ┌─────────┐ 4 ── button line
                   │ AQY210EH│
GND ────────────── 2 └─────────┘ 3 ── GND (button's other contact)
```

DIP-4, **viewed from above with the moulded dot top-left**:

| Position | Pin | Role |
|---|---|---|
| top left, at the dot | 1 | LED anode — via 470 Ω from the GPIO |
| bottom left | 2 | LED cathode — to the ESP's ground |
| bottom right | 3 | output |
| top right | 4 | output |

- **Pins 1 and 2 have a polarity**, it is a LED. 470 Ω from 3.3 V gives
  about 4.6 mA; the datasheet wants 5–10 mA and triggers from 1.2 mA.
- **Pins 3 and 4 are interchangeable.** The output is bidirectional, so
  there is no drain/source to get wrong.
- No gate resistor and no pulldown: those belong to the MOSFET version.

### N-channel MOSFET AO3400A — works, but fiddlier

```
GPIO ──[100 Ω]── gate ──┐
                        │  AO3400A (SOT-23)
          GND ──[10 kΩ]─┘   drain → button line
                            source → GND
```

SOT-23 seen from above: **pin 1 gate and pin 2 source on the same side,
pin 3 drain alone opposite**.

This is what we used first, and it works, but it cost us two long debugging
sessions:

- **The body diode.** Drain and source are not interchangeable. Mounted the
  wrong way round, the internal diode clamps the console's button line and
  the console will not power on at all — while everything looks fine.
  Check before wiring: multimeter in diode mode, red probe on the drain
  wire, black on ground, must read open.
- **Leakage.** The drain sits permanently on the console's button line. On
  one build a few tens of microamps were enough to hold the line down and
  kill the button.

The PhotoMOS has neither problem: the button line never touches the ESP's
circuit at all, not even through a drain.

## Powering the ESP

There is no buck converter here, so the ESP needs either 5 V or 3.3 V taken
from the console, present **in standby**, not only when the console is on.

- **Measure the candidate in all three states** — fully off, standby/rest,
  and running — before soldering.
- **Check it can actually supply the current.** A rail that reads 5 V
  unloaded can collapse under 80 mA: on the PS4 Pro the first point we
  picked dropped to 2 V and stopped the console from booting. A D1 mini
  draws 60–80 mA average with peaks several times that on Wi-Fi transmit.
- USB power from an external charger is a perfectly good fallback and keeps
  all load off the console (used on the PS3).

## Sense

Same idea as on the relay boards: find a point that is at 3.3 V only while
the console runs.

- **Over 3.3 V, use a divider.** On the PS4 Pro the sense comes from the
  5.2 V VBUS of a front USB port, through 10 kΩ / 20 kΩ, giving 3.47 V.
- Avoid rails that stay alive in standby for wake-on-network or wake-on-
  controller features; they never drop to 0 V and the console then can
  never be switched off from Home Assistant.

## Firmware

Nothing special. One GPIO as an output, one as the sense input, and a script
that pulses the output. The template in `firmware/` applies as-is; only the
press durations change from console to console.

**Press durations are not the same on every console.** A 300 ms pull is
enough to switch a PS3 or an Xbox 360 on, but a PS4 ignores anything shorter
than about 2 s when it is running. Measure yours by hand before writing the
values into the YAML.

## Bare ESP-12F variant

For consoles with no room at all, the ESP-12F module can be desoldered from
its carrier board (D1 mini, LoLin) and wired on its own. It then needs the
support parts the carrier provided:

| Pin | Resistor |
|---|---|
| EN (CH_PD) | 10 kΩ to 3.3 V — **mandatory**, no internal pull-up |
| GPIO15 | 10 kΩ to GND — **mandatory** |
| GPIO0 | 10 kΩ to 3.3 V — recommended |
| GPIO2 | 10 kΩ to 3.3 V — recommended |
| RST | 10 kΩ to 3.3 V — recommended |

Plus 100 nF between VCC and GND, close to the module.

**3.3 V only** on VCC — the bare module has no regulator, 5 V destroys it.
A working module draws about 60 mA at 3.3 V.

**Flash and test the OTA update before desoldering.** Once the module is off
its carrier there is no USB port left, and OTA is the only way back in.
