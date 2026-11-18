# Mega Drive

- Working with the same procedure as the other consoles.
- Follow the general steps in [README.md](README.md): always-on supply for
  the buck, switch contacts for J4, a 3.3 V sense point.
- Firmware: [`retropower_megadrive.yaml`](../../firmware/retropower_megadrive.yaml).

## Reset button in Home Assistant

Status: **working.** A "Reset" button in Home Assistant presses the
console's own Reset button. It does nothing while the console is off.

The relay stays in place for power — the Mega Drive's power switch is a
real switch. The Reset button is a push button, so it is driven like the
soft power buttons of the newer consoles: a **PhotoMOS AQY210EH** across
its two legs. See [soft-power-buttons.md](../soft-power-buttons.md).

| PhotoMOS pin | Goes to |
|---|---|
| 1 (the dot) | 470 Ω, then **GP20** of the ESP32-C3-Zero |
| 2 | a ground of the RetroPower board: **J6.2** is usually free |
| 3 and 4 | the two legs of the console's Reset button, either way round |

- **Finding the two legs**: console unplugged, continuity mode. With 4
  legs, they are joined in pairs inside the button; take two that only
  beep together while the button is pressed.
- **Why not a GPIO straight onto the Reset line**: the Mega Drive runs on
  5 V and its Reset line is pulled up to 5 V; the ESP32-C3 accepts 3.6 V at
  most. A resistor divider does not work either: it would load the Reset
  line itself, and the "press" would only pull it halfway down. The
  PhotoMOS keeps the 5 V away from the ESP entirely.
- **Never J5 for the ground**: J5 is the relay's second pole, not a ground.
  The grounds are J2.2, J3.2 and J6.2.
- Keep the PhotoMOS close to the Reset button, with short wires twisted
  together on the button side. The wire from GP20 can be longer.

### Which GPIO: GP20

On the Waveshare ESP32-C3-Zero, seen from its back (antenna on the left):

| Row | Pins (antenna side → USB-C side) |
|---|---|
| Top | GP6 · GP7 · GP8 · GP9 · **GP10** · GP18 · GP19 · **GP20** · GP21 |
| Bottom | **GP5** · GP4 · **GP3** · GP2 · GP1 · **GP0** · 3V3 · GND · 5V |

- **GP5 was the first choice, and a mistake**: it is the pin right next to
  the ceramic antenna. With a wire soldered on it, this console — one of
  the most stable on Wi-Fi until then — kept dropping off the network.
- **GP4** sits right next to GP3, the relay SET line: a solder bridge there
  would switch the console on at every Reset.
- **GP20**, at the USB-C end, far from the antenna, works. It is UART0 RX,
  but ESPHome logs over the USB-C on this module, so the pin is free.
  **Not GP21**, its neighbour: it outputs data at boot, which would press
  Reset at every power-up.
- When soldering on the top row, check **GP10** afterwards: it is the
  relay RESET line, three pins away. A disturbed joint there gives a
  console that switches on but no longer switches off.

### After flashing

ESPHome on ESP32 rolls back to the previous firmware if the new one has
not run for 60 s before a power cut. Flash over the air, then **leave the
board powered for 2 minutes** before unplugging it to close the console —
otherwise the Reset button disappears from Home Assistant after the next
power-up.

### Automation example

Press Reset 5 s after the console has been switched on (copy your own
entity IDs from Home Assistant):

```yaml
alias: Mega Drive - Reset 5 s after power-on
mode: single
triggers:
  - trigger: state
    entity_id: binary_sensor.megadrive_power_console_on_sensor
    from: "off"
    to: "on"
    for:
      seconds: 5
actions:
  - action: button.press
    target:
      entity_id: button.megadrive_power_reset
```
