# PlayStation 3 (fat)

Status: **working**. **No relay, no RetroPower board** — the power button is
a touch pad, so a single switching device across it is enough. See
[soft-power-buttons.md](../soft-power-buttons.md) for the general approach.

Built with a D1 mini and an AO3400A MOSFET. The PhotoMOS AQY210EH is a
drop-in replacement and is now the preferred part.

## DSW-001 button board — 10-pin connector

Measured on our unit. Pin 1 is the square pad.

| Pin | Signal | Measured |
|---|---|---|
| 1 | RMC_IN | |
| 2 | SW_PWM | |
| 3 | ? | drives the white LEDs |
| 4 | **POW_SW** | idles at about 5.6 V, pulled to ground = press |
| 5 | EJECT_SW | |
| 6 | **POW_LED** | 0 V off / 3.35 V on — this is the sense |
| 7 | STBY_LED | 3.3 V off / 0 V on (inverted, unused) |
| 8 | BD_LED | |
| 9 | **GND** | |
| 10 | **+5V_EVER** | 5 V in standby and when running |

The console's ground screw is the same net as pin 9 (0.08 V apart).

## Wiring

| From | To |
|---|---|
| Device output | pin 4 (POW_SW) and pin 9 (GND) |
| D2 (GPIO4) | via 470 Ω to the PhotoMOS LED, or via 100 Ω to the MOSFET gate |
| D5 (GPIO14) | pin 6 (POW_LED) — already 3.3 V, no divider |
| D1 mini G | pin 9 |

Pin 10 (+5V_EVER) is live in standby and can power the D1 mini. We ran the
tested build **from USB** instead, which keeps all load off the console.

## Press durations

| Action | Duration |
|---|---|
| On | 500 ms |
| Off | 4500 ms — a manual contact of about 4 s turns it off, margin added |

## Do not use the RetroPower PCB here

We first tried to reuse the compact board's Q1 to drive POW_SW, with the
relay left unpopulated. It failed, and the failure is worth recording.

With Q1 fitted and everything else disconnected, J1.4 (the gate node) sat at
**0.86 V** instead of 0 V — about 86 µA leaking from the 5.6 V drain into
the gate, the equivalent of roughly 55 kΩ. That was enough to pull POW_SW
down permanently and the console's own button stopped working. Removing Q1
restored everything; the same Q1 worked perfectly on a breadboard.

We never found the cause — flux residue or humidity under the SOT-23 is the
best guess. The lesson is simply that for a touch-button console there is
nothing to gain from the PCB: wire the device directly.
