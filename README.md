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

## Bill of materials

Full per-reference BOM (with placement notes) is in each version's own `BOM.csv` (`hardware/integrated/BOM.csv` / `hardware/compact/BOM.csv`). Same components and values on both versions, except J1 (compact version only, header for the flying wires to the ESP32) and the ESP32 module itself (soldered directly on the integrated version, wired via J1 on the compact one).

**On the PCB:**

| Ref | Part | Package | Notes |
|---|---|---|---|
| U1 | ESP32-C3-Zero (Waveshare) | 18-pin castellated module, 2.54mm pitch | Integrated version only — soldered to the back of the PCB |
| K1 | HFD2/003-M-L2-D (Hongfa) | DIP-16 (10 real pins) | Bistable 2xRT relay |
| Q1, Q2 | AO3400A | SOT-23 | N-channel MOSFET |
| D1, D2 | 1N4148WS | SOD-123 | Flyback diodes (relay coils) |
| D3 | 1N5819WS | SOD-123 | Reverse-polarity protection on RAW_IN |
| R1, R2 | 100R | 0805, 1/4W 5% | Series gate resistors |
| R3, R4 | 10k | 0805, 1/4W 5% | Gate pulldowns |
| C1 | 100µF / 16V | SMD electrolytic, 6.3x5.4mm | — |
| C2 | 100nF | 0805 ceramic | HF decoupling on 3V3 |
| J1–J6 | 2.54mm pin headers | 2 to 5 pins, vertical | See each version's wiring notes |

**Off the PCB (external, per console):**

- A buck converter module (raw 12V/8V → regulated 3.3V) — any small off-the-shelf buck board rated for the console's raw voltage works; test it unloaded before wiring it in.
- Hookup wire:
  - **Power lines** (raw 12V/8V to/from the buck, regulated 3V3 to J2): 0.5mm²/20-21AWG is plenty for these currents.
  - **Signal/GPIO lines** (console switch tap to J4/J5, POWER_SENSE tap to J6): thinner wire is fine here, e.g. 30AWG — negligible current, easier to route inside the console's case.

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
