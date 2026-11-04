# Xbox 360 Slim

Status: **working**. **No relay, no RetroPower board** — touch power button,
so a single switching device across it. See
[soft-power-buttons.md](../soft-power-buttons.md).

Built with a D1 mini. First with an AO3400A MOSFET, now with a **PhotoMOS
AQY210EH**: fewer parts, nothing to get backwards, same result.

## Front panel connector

The front panel board carries VCC 3.3 V, GND, **POWERSW**, the USB data
pair, and DATA/CLK (pulled up to 3.3 V in standby).

Shorting **POWERSW to ground** toggles the console. That is the pair the
device goes across.

Take the tap on the **motherboard side** of the ribbon rather than on the
front panel board: it keeps your wire away from the touch controller's
sensing electronics.

## Wiring

| From | To |
|---|---|
| Device output (pins 3/4, either way) | POWERSW and GND |
| D2 (GPIO4) | via 470 Ω to the PhotoMOS LED |
| D5 (GPIO14) | sense, see below |
| D1 mini 5V / G | permanent 5 V and ground from the console |

A short press switches the console on, another short press switches it off.

## Sense

The front panel documentation gives no usable idle/on point. We found one on
a **pin of the DVD drive connector**: 3.3 V while the console runs, 0 V when
it is off. No divider needed.

## Powering the ESP

The panel's 3.3 V could not supply the D1 mini — it browned out. We used a
**permanent 5 V** from the console into the D1 mini's `5V` pin instead,
which works. Do not plug USB at the same time.

## Pitfall that cost an evening: the front panel ribbon

After the mod the power button became hypersensitive and the console fired
random repeated presses — but **only with the front panel ribbon plugged
in**. With the ribbon unplugged, Home Assistant drove the console perfectly.

It was not the mod. The ribbon was simply **worn out**: these flex cables
crack at the folds and the contacts oxidise, and on a line coming out of a
touch controller an intermittent contact looks exactly like random presses.
Replacing the ribbon fixed it completely, with both the MOSFET and the
PhotoMOS.

**If the power button misbehaves after the mod, suspect the ribbon before
you suspect your wiring.**
