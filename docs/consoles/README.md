# Per-console installation notes

RetroPower reads the console's power state on `POWER_SENSE` and emulates a
press of its power button. *How* that press is emulated depends on the
console, and there are two different architectures.

## Two architectures

| | Bistable relay (the RetroPower board) | Single switching device, no relay |
|---|---|---|
| For | A real power switch that carries the rails | A soft / momentary / touch button |
| Current switched | up to ~1 A | a few µA of logic |
| Part | HFD2/003-M-L2-D | PhotoMOS AQY210EH (or an AO3400A MOSFET) |
| Keeps its state without power | yes | no — it is a pulse |
| Consoles | SNES, NES, Mega Drive, Master System, N64, GameCube, Saturn, Dreamcast, PS1 | PS2, PS3, PS4 Pro, Xbox OG, Xbox 360, Wii, Wii U |

The second one needs no PCB at all: an ESP (D1 mini or a bare ESP-12F), one
PhotoMOS and one resistor. It is written up in
[soft-power-buttons.md](../soft-power-buttons.md).

## Consoles

| Console | Build | Status | Notes |
|---|---|---|---|
| [SNES](snes.md) | Relay, integrated board | Working | First board built |
| [NES](nes.md) | Relay | Working | |
| [Mega Drive](mega-drive.md) | Relay | Working | A Reset button is designed but not built yet |
| [Master System](master-system.md) | Relay, integrated board | Working | **ESP32-C3-Zero swapped for a D1 mini** on an assembled board |
| [Nintendo 64](n64.md) | Relay | Working | **Two circuits to close (12 V + 3.3 V)** |
| [GameCube](gamecube.md) | Relay, compact board | Working | Switch = small PCB button |
| [PlayStation 1](ps1.md) | Relay, integrated board | Working | **Two poles** (7.5 V + 3.5 V) on the low-voltage side of the switch |
| [PlayStation 2 (fat)](ps2.md) | Relay | Working | **Momentary button**: the relay simulates a press (short = on / reset, long = off). Reset is disabled by the console once a hard drive is connected |
| [PlayStation 3](ps3.md) | PhotoMOS + D1 mini | Working | Everything on the DSW-001 connector. **Do not use the compact PCB here** |
| [PlayStation 4 Pro](ps4-pro.md) | PhotoMOS + D1 mini | Working | Sense on a front USB VBUS, through a divider |
| [Xbox OG](xbox-og.md) | PhotoMOS + D1 mini | Working | Standby and sense voltages depend on the board revision |
| [Xbox 360 Slim](xbox360-slim.md) | PhotoMOS + D1 mini | Working | Tap POWERSW on the motherboard side |
| [Wii](wii.md) | ESP-12F + PhotoMOS | Working | **Active-high power button**: across TP112 and a 3.3 V pad, not to ground |
| [Wii U](wii-u.md) | ESP-12F + PhotoMOS | Working | Bare module soldered straight to the test points |

Saturn and Dreamcast are also running, with the standard relay procedure
below and nothing console-specific worth recording.

## General procedure (relay version)

1. **Find the always-on supply.** Measure with the multimeter in DC volts,
   console off but its power brick plugged in. You need a point that stays
   live in this state: it feeds the buck converter (raw 12 V / 9 V) so the
   ESP32 keeps running when the console is off.
2. **Find the power switch contacts.** Brick unplugged, continuity mode: the
   pair must be open when the console is off and closed when it is on. Wire
   J4 COM (square pad) and J4 NO (last round pad) across it. J4 NC (middle
   pad) stays unused.
3. **Find a POWER_SENSE point** at about 3.3 V that drops to 0 V when the
   console is off. Never connect more than 3.3 V to J6 (GP0 is not 5 V
   tolerant, there is no divider on the board).
4. **Flash** the ESP32 over USB the first time (hold BOOT while plugging in
   if the port is not detected), then use OTA. One unique static IP per
   console.

For the no-relay version, the procedure is in
[soft-power-buttons.md](../soft-power-buttons.md).

## Pitfalls we hit

- **Bistable relay.** It keeps its last position without power. If you
  measure continuity on a switch while the relay is still closed, you are
  measuring the relay, not the switch. Reset it first (send "off" from Home
  Assistant) and disconnect J4/J5 when measuring.
- **Check every ESP32 pin you use is actually soldered**: GP0 (sense), GP3
  (SET), GP10 (RESET). A neighbouring pin soldered by mistake gives
  intermittent failures that look like firmware or WiFi problems.
- **Relay position after a power cut.** If the relay is left closed, the
  console turns on as soon as it is plugged in. The firmware template resets
  the relay at boot when the sense input says the console is off.
- **Momentary (soft) power buttons** (PS2, and likely others): the button
  contact is not a switch that stays closed. Use a script that closes the
  relay for a moment and reopens it, and press only if POWER_SENSE says the
  console is not already in the requested state. See [PS2](ps2.md).
- **A rail that measures 5 V unloaded is not necessarily a 5 V supply.** On
  the PS4 Pro the first candidate point collapsed to 2 V once the D1 mini
  was drawing from it, and the console would not boot. On the Xbox 360 the
  front panel's 3.3 V browned out on Wi-Fi peaks. Measure again **with the
  ESP connected and running**, not just with a multimeter on an idle point.
- **An always-on standby rail cannot be used as the sense.** It never drops
  to 0 V, so Home Assistant would see the console as permanently on and
  could never switch it off. This bites on the Wii (3V3 Standby) and the
  Wii U (connected standby stays on the network).
- **Worn front-panel ribbons.** On the Xbox 360 Slim, a tired flat cable
  made the power button hypersensitive and fired random repeated presses —
  only when the ribbon was plugged in. Hours were spent looking for coupling
  between the signal wires; replacing the ribbon fixed it outright. If the
  symptom only appears with one connector in place, suspect the connector.
- **Press durations are per-console and must be measured.** 300 ms on a PS4
  Pro, 500 ms on a PS3, 8 s for a PS4 full shutdown. The same value does not
  carry over.
- **Power-off flash on the screen** (analogue video through a scaler) is
  cosmetic. A 100 ms RESET pulse reduced it.
- **Continuity mode is not a plain wire.** The multimeter injects a small
  current out of the red probe. A console that powers on with red on the
  button line and black on ground may be reacting to that voltage, not to a
  short. Swap the probes, or use a plain wire, before concluding. This hid
  the Wii's active-high button for an evening.
- **Not every button pulls to ground.** Measure both pads of the button in
  volts with the console in standby. If the "ground" side reads 3.3 V, the
  PhotoMOS goes across the two pads, not to ground. See [Wii](wii.md).
- **Probing a live console:** a slipping probe can trip the brick's
  protection. Probe the ground first, then the test point, and do not slide.
- **Never plug the ESP's USB in while the console is powering it.** On the
  no-relay builds the 5 V pin is wired straight to the motherboard.
