# Per-console installation notes

RetroPower emulates the console's power button with a bistable relay (K1),
and reads the console's power state on `POWER_SENSE` (J6). The procedure is
the same on every console; only the measurements differ.

| Console | Board used | Status | Notes |
|---|---|---|---|
| [SNES](snes.md) | Integrated | Working | First board built |
| [GameCube](gamecube.md) | Compact | Working | Switch = small PCB button |
| [NES](nes.md) | see file | Working | |
| [Mega Drive](mega-drive.md) | see file | Working | |
| [Nintendo 64](n64.md) | see file | Working | **Two circuits to close (12 V + 3.3 V)** |
| [PlayStation 2 (fat)](ps2.md) | see file | Working | **Momentary button**: the relay simulates a press (short = on / reset, long = off). Reset is disabled by the console once a hard drive is connected |

## General procedure

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
- **Power-off flash on the screen** (analogue video through a scaler) is
  cosmetic. A 100 ms RESET pulse reduced it.
- **Probing a live console:** a slipping probe can trip the brick's
  protection. Probe the ground first, then the test point, and do not slide.
