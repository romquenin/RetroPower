# GameCube

- **Board:** Compact (ESP32 on flying wires).
- **Power input:** the console takes 12 V from its brick; about 12.35 V was
  measured at the supply connector with the console off, which makes it a
  good buck input.
- **Power switch:** a small separate PCB carries the button. The two big
  square pads only hold the button mechanically (no continuity). The two
  small round inner pads are the contacts: open when released, closed when
  pressed (console on). The switch latches like the SNES one, so the relay
  replaces it directly.
- **Wiring:** J4 on those two small pads (the order does not matter), 0.25 mm²
  wire is enough for the signal side.
