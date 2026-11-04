# PlayStation 4 Pro (NVA-001)

Status: **working**. **No relay, no RetroPower board** — soft power button.
See [soft-power-buttons.md](../soft-power-buttons.md).

Built with a D1 mini and an AO3400A MOSFET; the PhotoMOS AQY210EH is a
drop-in replacement.

The motherboard is marked `1-981-472-11 NVA-001`, and everything below was
measured on **side B**.

## Power button

The button pads are on the ribbon going to the front board; shorting the
pair toggles the console, as on the PS3 and the Xbox 360. The device output
goes across them.

## Sense: the VBUS of a front USB port

The front USB ports are USB **3.0**, so each has **9 pads**, not 4: a row of
5 for the SuperSpeed pairs and a row of 4 for USB 2.0. The row of 4, the one
closest to the board edge, carries VBUS, D−, D+ and GND. Probe the four with
the black probe on a shield tab: the one at about 5 V is VBUS.

Measured: **5.20 V with the console running, 0 V when it is off.**

> Set **"Supply Power to USB Ports" in rest mode to OFF** in the console's
> settings, otherwise VBUS stays live in rest and the sense never drops.

5.2 V is too much for the ESP, so it goes through a divider:

```
VBUS ──[10 kΩ]──┬── D5 (GPIO14)
                │
          [10 kΩ]
                │
          [10 kΩ]
                │
               GND
```

5.20 × 20 / 30 = **3.47 V**, inside the ESP8266's 3.6 V limit. Three 10 kΩ
resistors, two of them in **series** for the bottom leg — in parallel they
would give 5 kΩ and 2.5 V, which sits right on the logic threshold.

## Powering the ESP

A permanent 5 V from the motherboard, into the D1 mini's `5V` pin. Measured
on the point we used: **4.87 V in rest, 4.67 V fully off, 4.66 V running** —
present in all three states, which is what matters.

**Pick a point that can supply the current.** The first candidate we tried
read 4.87 V unloaded but collapsed to 2 V with the D1 mini on it, and the
console would not start at all. Measure again with the load connected.

One ground wire is enough: the D1 mini's `G` *is* the console's ground, so
the bottom of the divider simply goes to the nearest ground.

## Press durations

| Action | Duration | Result |
|---|---|---|
| On | 300 ms | powers on, or wakes from rest |
| Off | 2 s | the console ignores anything shorter while it runs |
| Forced off | 8 s | full shutdown, two beeps |

A short press while the console runs puts it in **rest mode**, not off. Both
behaviours are usable: with USB power disabled in rest, the sense drops to
0 V either way, so Home Assistant shows "off" in both cases. Rest wakes in
seconds; a full shutdown takes about a minute to boot.

The Home Assistant switch is wired to the 8 s press, with separate buttons
for the short press and for rest.
