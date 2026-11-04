# Mega Drive

- Working with the same procedure as the other consoles.
- Follow the general steps in [README.md](README.md): always-on supply for
  the buck, switch contacts for J4, a 3.3 V sense point.

## Planned: a Reset button in Home Assistant

**Not installed yet** — written down so the wiring is ready.

The Mega Drive's Reset button is a push button that pulls the `/RESET` line
to ground, so it can be driven exactly like the soft power buttons on the
newer consoles: a **PhotoMOS AQY210EH** across the two button pads, on a
spare GPIO. See [soft-power-buttons.md](../soft-power-buttons.md).

- The relay stays in place for power — the Mega Drive's power switch is a
  real switch.
- Pick a GPIO with no boot constraints: **GPIO4 or GPIO5** on the
  ESP32-C3-Zero. Avoid GPIO2, GPIO8 and GPIO9.
- `GPIO → 470 Ω → pin 1`, `pin 2 → the board's ground`, `pins 3 and 4
  across the button` (either way round).
- The console's logic runs at 5 V and the reset line is probably pulled up
  to 5 V. That is exactly why the PhotoMOS is the right part here: the line
  never touches the ESP's circuit.
- Identify the two pads with the console unplugged: the one that sounds
  with ground is the return, the other is the reset line.

Firmware side, a 200 ms pulse guarded by the sense so it does nothing while
the console is off:

```yaml
output:
  - platform: gpio
    pin: GPIO4
    id: reset_pin

script:
  - id: pulse_console_reset
    then:
      - output.turn_on: reset_pin
      - delay: 200ms
      - output.turn_off: reset_pin

button:
  - platform: template
    name: "${friendly_name} - Reset"
    on_press:
      - if:
          condition:
            binary_sensor.is_on: power_sense
          then:
            - script.execute: pulse_console_reset
```
