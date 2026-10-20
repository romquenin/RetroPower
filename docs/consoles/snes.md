# SNES

- **Board:** Integrated (ESP32-C3-Zero soldered on the back). First board built.
- **Firmware:** `firmware/retropower_template.yaml`, static IP `192.168.2.230`.
- **Wiring:** J2 = buck 3.3 V output, J4 = COM + NO across the console's
  power switch, J6 = 3.3 V sense point.

## Lessons learned

- An unsoldered **GP0** meant Home Assistant never saw the console state.
- An unsoldered **GP10** (a neighbouring pin was soldered instead) made the
  power-off command fail intermittently. Re-soldering GP10 fixed it and the
  sense now follows immediately.
- D1/D2 are mounted rotated 180° compared to the silkscreen (see the root README).
