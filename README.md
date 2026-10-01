# RetroPower

Home Assistant-controlled power module for retro consoles, built around an ESP32-C3 — 2-layer PCB (KiCad), with a relay that emulates the console's power button for remote on/off.

## Two PCB versions

### `hardware/integrated/` — integrated version (recommended)
The ESP32-C3-Zero module (Waveshare, 18 castellated pins) is **soldered directly to the back of the PCB** — no flying wires. The antenna ends up on the outer edge of the board, completely clear of any copper/metal on both sides, for the best possible WiFi/Bluetooth reception.

- Dimensions: 53.335 x 32.75 mm
- Official KiCad DRC: 0 errors / 0 warnings (v4)
- See `README.md` in this folder for the changelog and the pin-spacing verification procedure to run before soldering the module for good.

### `hardware/compact/` — compact version (fallback)
The ESP32-C3-Zero module is connected via flying wires (not soldered directly onto the PCB). Immune to dimensional variation between modules — useful as a fallback if the integrated version ever runs into a physical compatibility issue.

- Dimensions: 40.45 x 32.75 mm
- Official KiCad DRC: 0 errors / 0 warnings (v11)
- See `README.md` and `WIRING.md` in this folder.

Each folder contains: the `.kicad_pcb`/`.kicad_pro` files, the gerbers (folder + zip), the component position file (`_pos.csv`), the BOM (`BOM.csv`), a rendered image of the routed board, and a `README.md` explaining the design choices.

## Firmware

`firmware/retropower_template.yaml` — generic ESPHome template, to be duplicated for each console (change `device_name` / `friendly_name`). Pinout used:

- GPIO0 — `POWER_SENSE` (reads the console's 3V3 rail)
- GPIO3 — `RELAY_SET` (pulse → turns on, via Q1)
- GPIO10 — `RELAY_RESET` (pulse → turns off, via Q2)

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
