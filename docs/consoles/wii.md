# Wii

Status: **prepared, not installed yet.** The module is built and validated
on the bench (flashed, OTA tested, 62 mA at 3.3 V, visible in Home
Assistant), but nothing is soldered inside the console yet. The rails below
come from Shank's Wii Super Thread and still need to be confirmed with a
multimeter on the actual board.

Planned build: **bare ESP-12F + PhotoMOS AQY210EH**, no relay — the Wii's
power button is a momentary push button. See
[soft-power-buttons.md](../soft-power-buttons.md).

## Two different 3.3 V rails — do not mix them up

This is the whole difficulty on this console.

| Rail | Behaviour | Use |
|---|---|---|
| **3V3** (main) | *"only on while system is on"* | **sense** |
| **3V3 Standby** | *"always on, even when the console is off"* | could power the ESP |

There is a **3.3 V test point on the back of the board** for the main rail —
the Wii has several labelled test points underneath, used by the
portablizing community.

The standby regulator sits **next to the MX chip** on the front side. Its
package depends on the board revision: switching on RVL-60, RVK-01, RVK-02
and RVO-01, linear on RVL-01, 20, 30 and 40.

**Taking the sense from 3V3 Standby would be a dead end**: it never drops to
0 V, so Home Assistant would see the console as permanently on and could
never switch it off.

## Powering the module

Two candidates, neither confirmed yet:

- **3V3 Standby**, straight onto VCC — right voltage, no converter, no
  space taken. The risk is current: that rail feeds the Bluetooth module
  and is sized for a few milliamps. A 470 µF close to the module helps a
  lot here, since the regulator then only has to supply the average.
- **VCC 12 V** from the external brick, which is present whenever the
  console is plugged in, through a small buck.

**Test to run after wiring the standby option:** check that the console
still powers on **from a Wiimote**. The Bluetooth module shares that rail,
so if it starts misbehaving, the ESP is drawing too much.

There is **no permanent 5 V** on this console: the 5 V rail feeds the USB
ports, the GameCube rumble pins and the fan transistor, all of which are
only alive when the console runs.

Sources: Shank's Wii Super Thread, on
[BitBuilt](https://bitbuilt.net/forums/threads/shanks-wii-super-thread.66/)
and [ModRetro](https://forums.modretro.com/threads/shanks-wii-super-thread.14659/).
