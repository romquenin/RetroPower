# RetroPower

Home Assistant-controlled power module for retro consoles, built around an ESP32-C3 — 2-layer PCB (KiCad), with a relay that emulates the console's power button for remote on/off.

Consoles with a **real power switch** (SNES, NES, Mega Drive, Master System, N64, GameCube, Saturn, Dreamcast, PS1) use this board. Consoles with a **soft / momentary / touch button** (PS2, PS3, PS4 Pro, Xbox 360, Wii, Wii U) need no PCB at all — just an ESP, one PhotoMOS and one resistor. That variant is documented in [`docs/soft-power-buttons.md`](docs/soft-power-buttons.md).

## Two PCB versions

### `hardware/integrated/` — integrated version (recommended)
The ESP32-C3-Zero module (Waveshare, 18 castellated pins, **antenna version isolated at the end of the board**, see the BOM warning) is **soldered directly to the back of the PCB** — no flying wires. The antenna ends up on the outer edge of the board, completely clear of any copper/metal on both sides, for the best possible WiFi/Bluetooth reception.

- Dimensions: 53.335 x 32.75 mm
- Official KiCad DRC: 0 errors / 0 warnings (v4)
- See `README.md` in this folder for the changelog and the pin-spacing verification procedure to run before soldering the module for good.

<img width="1143" height="702" alt="sm_green_top (1)" src="https://github.com/user-attachments/assets/a69a00d4-70a4-4928-a85d-eebd806ac32e" />


### `hardware/compact/` — compact version (fallback)
The ESP32-C3-Zero module is connected via flying wires (not soldered directly onto the PCB). Immune to dimensional variation between modules — useful as a fallback if the integrated version ever runs into a physical compatibility issue.

- Dimensions: 40.45 x 32.75 mm
- Official KiCad DRC: 0 errors / 0 warnings (v11)
- See `README.md` and `WIRING.md` in this folder.

<img width="1123" height="910" alt="sm_green_top" src="https://github.com/user-attachments/assets/41fc7552-13aa-4425-9eb9-e23fb433d2f4" />


Each folder contains: the `.kicad_pcb`/`.kicad_pro` files, the gerbers (folder + zip), the component position file (`_pos.csv`), the BOM (`BOM.csv`), a rendered image of the routed board, and a `README.md` explaining the design choices.

## Bill of materials

Full per-reference BOM (with placement notes) is in each version's own `BOM.csv` (`hardware/integrated/BOM.csv` / `hardware/compact/BOM.csv`). Same components and values on both versions, except J1 (compact version only, header for the flying wires to the ESP32) and the ESP32 module itself (soldered directly on the integrated version, wired via J1 on the compact one).

**On the PCB:**

| Ref | Part | Package | Notes |
|---|---|---|---|
| U1 | ESP32-C3-Zero (Waveshare) ⚠️ | 18-pin castellated module, 2.54mm pitch | **Version with the antenna at the end of the board, isolated from the other components** (see warning below). Integrated version only: soldered to the back of the PCB |
| K1 | HFD2/003-M-L2-D (Hongfa) | DIP-16 (10 real pins) | Bistable 2xRT relay |
| Q1, Q2 | AO3400A | SOT-23 | N-channel MOSFET |
| D1, D2 | 1N4148WS | SOD-123 | Flyback diodes (relay coils). **Orientation: the stripe (cathode) goes on the OPEN side of the rectangle on the silkscreen** |
| D3 | 1N5819WS | SOD-123 | Reverse-polarity protection on RAW_IN. **Orientation: the stripe (cathode) goes on the CLOSED side of the rectangle on the silkscreen** |
| R1, R2 | 100R | 0805, 1/4W 5% | Series gate resistors |
| R3, R4 | 10k | 0805, 1/4W 5% | Gate pulldowns |
| C1 | 100µF / 16V | SMD electrolytic, 6.3x5.4mm | — |
| C2 | 100nF | 0805 ceramic | HF decoupling on 3V3 |
| J1–J6 | 2.54mm pin headers | 2 to 5 pins, vertical | See each version's wiring notes |

> ⚠️ **Pick the right ESP32-C3 module.** Use the **Waveshare ESP32-C3-Zero** whose ceramic antenna sits **at the end of the board, set apart from the other components**. The PCB is designed so this antenna ends up on the outer edge, clear of any copper. Look-alike boards (clones, "ESP32-C3 Super Mini"…) where the antenna sits among the components, or a different pinout, will give poor Wi-Fi reception and may not fit the footprint. Check the product photos before ordering.

### ESP32-C3-Zero pin order (check before ordering)

<img width="827" height="591" alt="Sans titre-1" src="https://github.com/user-attachments/assets/4ab96921-4050-4042-9509-2f850d7f2c30" />


The footprint matches the **pin order of the Waveshare ESP32-C3-Zero**. Some look-alike modules use the same size but a **different pin order**: with those, the power and GPIO pins end up in the wrong place. Compare your module with the order below before soldering.

Module seen **from its back side** (the side soldered to the PCB), antenna on the left, USB-C on the right:

| Row | Pins (antenna side → USB-C side) |
|---|---|
| Top (pins 10 → 18) | GP6 · GP7 · GP8 · GP9 · **GP10** · GP18 · GP19 · GP20 · GP21 |
| Bottom (pins 9 → 1) | GP5 · GP4 · **GP3** · GP2 · GP1 · **GP0** · **3V3** · **GND** · 5V |

Pins used by RetroPower:

| Module pin | Signal | Role |
|---|---|---|
| 2 · GND | GND | Common ground |
| 3 · 3V3 | 3V3 | Power from the 3.3 V buck (5V pin stays unconnected) |
| 4 · GP0 | POWER_SENSE | Reads the console state |
| 7 · GP3 | RELAY_SET | Relay SET (turn on) |
| 14 · GP10 | RELAY_RESET | Relay RESET (turn off), also drives the module's RGB LED |

<!-- Photo of the correct module (back side, pin labels visible): add it as docs/images/esp32-c3-zero-pinout.jpg and uncomment the line below.
![ESP32-C3-Zero pinout](docs/images/esp32-c3-zero-pinout.jpg)
-->

Full details and the pin-spacing check: [`hardware/integrated/README.md`](hardware/integrated/README.md).

**Off the PCB (external, per console):**

- A buck converter module (raw 12V/8V → regulated 3.3V) — any small off-the-shelf buck board rated for the console's raw voltage works; test it unloaded before wiring it in.
- Hookup wire:
  - **Power lines** (raw 12V/8V to/from the buck, regulated 3V3 to J2): 0.5mm²/20-21AWG is plenty for these currents.
  - **Signal/GPIO lines** (console switch tap to J4/J5, POWER_SENSE tap to J6): thinner wire is fine here, e.g. 30AWG — negligible current, easier to route inside the console's case.

## Firmware

ESPHome configs, in `firmware/`. Duplicate the template that matches your build and change `device_name` / `friendly_name` / the static IP — **one unique IP per console**.

| File | For |
|---|---|
| `retropower_template.yaml` | Relay board + ESP32-C3-Zero (validated on a SNES) |
| `retropower_template_esp8266.yaml` | Relay board + D1 mini (validated on a Master System) |
| `retropower_ps2.yaml` | PS2 fat — relay, momentary button |
| `retropower_ps4.yaml` | PS4 Pro — PhotoMOS, no relay |

Pinout on the **ESP32-C3** board:

- GPIO0 — `POWER_SENSE` (reads the console's 3V3 rail)
- GPIO3 — `RELAY_SET` (100 ms pulse → turns on, via Q1)
- GPIO10 — `RELAY_RESET` (100 ms pulse → turns off, via Q2)

Same board with a **D1 mini** soldered in instead (ESP8266: GPIO0 is a boot strapping pin, GPIO3 is the serial RX and GPIO10 is not brought out, so the three pins have to move):

- GPIO14 / `D5` — `POWER_SENSE`
- GPIO5 / `D1` — `RELAY_SET`
- GPIO4 / `D2` — `RELAY_RESET`

The `D0`–`D8` labels are silkscreen only and have nothing to do with the GPIO numbers — always write the GPIO number in the YAML.

On the **no-relay** builds, a single `output` drives the PhotoMOS (`GPIO4` / `D2`, through a 470 Ω) and `GPIO14` / `D5` reads the sense. The press duration is what distinguishes power-on, standby and forced shutdown, and it has to be measured per console.

## Per-console notes

Measurements, wiring and lessons learned for each console tested so far are in [`docs/consoles/`](docs/consoles/README.md).

## Related projects

- [`projects/toslink-switch-wifi/`](projects/toslink-switch-wifi/README.md) — Wi-Fi control of a CSL 41811 Toslink audio switch (ESPHome on a D1 mini, MOSFET on the IR-jack signal line), so the audio input follows the console that is running.

## Generation scripts (KiCad / Python)

`scripts/` contains the Python scripts (using the `pcbnew` API) used to generate and route each board, plus the verification scripts (clearance, holes, connectivity, board-edge clearance, silkscreen, component-body overlap) used alongside KiCad's official DRC.

- `scripts/integrated/`: `build_integrated.py` (placement + footprints), `route_integrated.py` (initial routing), `fix_net_integrated.py` (targeted routing fixes)
- `scripts/compact/`: `build_compact_v3.py`, `route_grid_compact5.py`
- `scripts/checks/`: verification scripts shared by both versions

Requires KiCad 7 (headless `pcbnew` API) and Python 3.

## How it works

The module emulates pressing the console's power button through two separate pulses (SET/RESET) driven by two MOSFETs (Q1/Q2) that control the two coils of a bistable relay (K1) — the relay stays in the chosen state with no continuous power draw. A sense tap (`POWER_SENSE`) lets the ESP32 read the console's actual power state for Home Assistant.

## Power supply

The buck converter (console's raw 12V/8V → regulated 3.3V) is **external**, not integrated onto the PCB. See each version's `README.md`/`WIRING.md` for the exact wiring (`J2` = regulated 3.3V input, `J3` = raw tap + reverse-polarity protection).

## Disclaimer

These files are provided as-is, with no warranty. Always re-run KiCad's official DRC before ordering a batch of PCBs, and check the 3V3 rail with a multimeter before soldering an ESP32 module in for good.

## Assembly notes (validated on a SNES, integrated board)

- **D1/D2 (flyback, 1N4148WS):** in KiCad's `D_SOD-123` footprint pad 1 is the *cathode*. The cathode must go to 3V3, so mount D1/D2 **rotated 180° vs the silkscreen** (stripe toward the 3V3 pad). **D3** is mounted as per the silkscreen.
- **GP0 (U1 pin 4) must be soldered** - it carries POWER_SENSE. Without it Home Assistant never sees the console state.
- Connect the J6 sense wire to the console's 3.3V rail; grounds must be common (buck GND on the console motherboard).
- J4: use COM (square) + NO, in parallel with the original power switch.
