RetroPower - Central module, INTEGRATED version (ESP32-C3-Zero soldered to the BACK of the PCB)
====================================================================================
Dimensions: 53.335 x 32.75mm (the "compact" version with flying wires,
40.45 x 32.75mm, remains AVAILABLE AS A FALLBACK -- see below).

FIX v4 -- J4 reference label restored
--------------------------------------------------------------------
In v3, J4's reference had been hidden for lack of space. At the user's
request: reused the same treatment as J5/J6 just below (label offset to
the left of the connector instead of above it) -- same solution, same
visual result, J4 has its reference label back.
The whole board was fully rerouted and re-verified after this change (one
net touched by the new routing, Q2_GATE, was redone with a more generous
clearance): 0 violations across the 5 checks.

FIX v3 (official DRC run on v2) -- 3 warnings fixed
--------------------------------------------------------------------
1. [text_height] the "U1 -- MOUNT ON BACK" note was 0.6mm tall, below the
   0.8mm minimum required by the PCB's design rules.
2. [silk_over_copper] that same note, placed vertically in the narrow gap
   between U1 and K1 (0.85mm), overflowed onto K1's solder mask -- that
   gap is in fact too narrow for any text regardless of its size.
   -> Fixed: note shortened ("U1: MOUNT ON BACK OF PCB"), switched back
   to horizontal at 0.8mm, moved into the clear space BELOW U1 and ABOVE
   C1 (~1.585mm tall, plenty of room).
3. [silk_overlap] J4's reference field, repositioned to clear R1, was
   actually overlapping J4's own body -- the area around J4/R1/J5 is too
   tight in every direction to fit a label there.
   -> Fixed: J4's reference hidden (like U1's), purely cosmetic -- it
   stays in the BOM and the position file.

The whole board was re-verified and rerouted after these changes: 0
violations across the 5 checks (clearance, holes, connectivity, board
edge, silkscreen); the same already-known 0.25-0.30mm close calls between
component bodies (K1/J3/D3/D1, J5/J6) remain, identical to the previous
version.

WHAT CHANGED IN v2 COMPARED TO THE INITIAL v1
--------------------------------------------------------------------
Three changes compared to the previous integrated version:

1. MOUNTED ON THE BACK OF THE PCB (no longer on the component side)
   After discussion about pin orientation: the Waveshare datasheet that
   gives the pinout detail (5V/GND/3V3/GP0../GP21) is a view of the BACK
   of the module. Two mounting options are possible:
     - module's component side facing up (same side as K1, Q1...): this
       would have required MIRRORING this back view before placing the
       pads.
     - module's component side facing DOWN (soldered to the back of the
       PCB): the back view can be used AS-IS, with no mirroring.
   This second option is the one used here -- the pinout from the
   previous delivery was therefore correct, but ONLY for back-mounting,
   not component-side mounting as mistakenly stated at the time.
   Additional benefit: the component side of the PCB stays completely
   clear under the antenna (no trace or pad from any other component
   nearby), for the best possible RF isolation.
   Consequence: U1 has no silkscreen outline of its own (no outline or
   text printed on the back, to avoid extra JLCPCB manufacturing cost) --
   a note "U1 (ESP32-C3-Zero) -- MOUNT ON BACK OF PCB" is printed on the
   FRONT silkscreen, next to U1's location, so this isn't forgotten
   during assembly.

2. 2-ROW PIN SPACING CORRECTED (15.24mm instead of 18mm)
   The first estimate (18mm) was based on the module's total body width
   -- too large. You measured the real spacing via photo overlay
   (Photoshop, calibrated on the 2.54mm horizontal pitch, cross-checked
   against K1's footprint): ~15.43mm, very close to 15.24mm = 6 x 2.54mm
   (a "round" value on the same grid, likely the real manufacturer spec).
   This is the value used here. AS ALWAYS: to be confirmed with a new
   photo overlay once the physical PCB is received, before soldering the
   module for good (see the verification procedure below).

3. U1 REPOSITIONED ABOVE C1, PCB SHORTENED BY 10.615mm
   Thanks to the corrected pin spacing (U1 much more compact in height),
   U1 now fits above C1 without making the board taller. Its right edge
   (USB-C side) is aligned with C1's right edge. K1, Q1, Q2, D2, C1, C2,
   J2, J4, J5, J6 moved closer to U1 (offset reduced from 23.5mm to
   12.885mm); J3, D3, D1, R1 (just above K1) moved back a bit further
   (18.885mm) to clear U1 -- they remain X-overlapped with K1 but
   Y-separated, exactly as in the original layout already validated by
   the official DRC. Result: the board goes from 63.95mm to 53.335mm in
   length (-10.615mm).

MODULE ORIENTATION -- REMINDER
--------------------------------------------------
The module is rotated 90 deg relative to its "natural" position (USB-C
normally at the top on its product page): here, **USB-C points to the
right** (towards K1/the rest of the board) and the **antenna ends up on
the left**, on the board's outer edge -- the most clear spot possible
from any copper or metal, on BOTH sides of the PCB now (see point 1
above), for the best possible WiFi/Bluetooth reception.

U1 PINOUT (ESP32-C3-Zero module, mounted on the BACK of the PCB)
------------------------------------------
Viewed from the back of the PCB (the side where the module is soldered),
once soldered in the orientation described above (antenna on the left,
USB-C on the right):

  TOP row (pins 10 to 18, from left/antenna to right/USB-C):
    GP6 - GP7 - GP8 - GP9 - GP10 - GP18 - GP19 - GP20 - GP21

  BOTTOM row (pins 9 to 1, from left/antenna to right/USB-C):
    GP5 - GP4 - GP3 - GP2 - GP1 - GP0 - 3V3 - GND - 5V

Pin 1 (5V) marked by a square pad, bottom-right corner (near USB-C) --
same convention as every other connector on the board.

Connections used:
  Pin 3  (3V3, bottom row)  <- power from the 3.3V buck
  Pin 2  (GND, bottom row)  <- common ground
  Pin 4  (GP0, bottom row)  -> SENSE_MID (reads POWER_SENSE)
  Pin 7  (GP3, bottom row)  -> SET_CTRL (relay SET command)
  Pin 14 (GP10, top row)    -> RESET_CTRL (relay RESET command)

All other pins (1/5V, 5,6,8,9,10,11,12,13,15,16,17,18) remain
UNCONNECTED -- that's normal, they aren't used in this setup.

Powering through pin 3 rather than USB: this is the standard method for
this type of module (the "3V3(OUT)" pin is actually the output of the
onboard LDO regulator, but feeding it directly with an already-clean
3.3V supply -- our buck -- is common and safe practice, as long as the
5V pin stays unconnected at the same time).

Accepted side effect: GP10 is also the pin that drives the module's
built-in RGB LED (WS2812) -- it will therefore blink along with every
relay RESET command.

********************************************************************
* TO VERIFY BEFORE SOLDERING FOR GOOD -- PIN SPACING                *
********************************************************************
The 15.24mm figure used here comes from a photo-overlay measurement
(accurate, but not a physical measuring instrument). BEFORE soldering
the module onto this board for good:
  1. First solder the pin header onto the module's own castellated
     half-holes (not onto the PCB yet).
  2. Measure the REAL spacing between the two pin rows with calipers
     (center to center), OR redo a photo overlay once the physical PCB
     is in hand (same method as before: calibrate on the 2.54mm pitch,
     compare against the PCB).
  3. Compare against 15.24mm. If the difference is significant
     (>0.3-0.4mm), let me know before soldering onto the PCB -- the pads
     would need adjusting and a targeted reroute, which is quick to fix.

WHAT WAS VERIFIED ON THIS VERSION
-------------------------------------------
- Distance to the board outline (0.5mm required): 0 violations.
- Electrical clearance (exact pad geometry, vias included): 0 violations
  across 475 elements.
- Real connectivity: 0 open circuits, 0 dangling ends.
- Hole-to-hole spacing: 0 violations across 87 holes.
- Silkscreen overlap: 0 overlaps.
- Component body overlap: the same already-known and accepted
  0.25-0.30mm close calls from the original compact version (validated
  by the official DRC) remain -- nothing new introduced by this
  repositioning (checked component by component).

As always: this is my own verification, NOT a substitute for KiCad's
official DRC -- re-run it on this file before ordering.

YOU CAN ALWAYS GO BACK TO THE COMPACT VERSION
---------------------------------------------------
The flying-wire version (40.45 x 32.75mm, ESP32 module attached
separately) remains available and fully validated (official DRC 0/0) --
nothing has been removed or modified in those files.

WHAT'S LEFT TO DO BEFORE ORDERING
---------------------------------------------
1. The module fit-check test described above (the most important point
   for this version).
2. Re-run KiCad's official DRC on this file.
3. Check that 53.335 x 32.75mm fits the intended enclosure.
4. The buck stays external and MUST be tested unloaded before wiring it
   in.
5. Before soldering the ESP32-C3-Zero for good: measure the voltage on
   the PCB's 3V3 rail with a multimeter (between a 3V3 pad and a GND
   pad) BEFORE soldering the module in -- you should read ~3.3V, not
   ~12V.

FILES PROVIDED
-------------------
- RetroPower_Integrated.kicad_pcb: the complete PCB (open in KiCad)
- RetroPower_Integrated.kicad_pro: minimal project file
- gerbers_RetroPower_Integrated.zip: Gerbers + drill + position file
- RetroPower_Integrated_pos.csv: position/orientation of each component
- BOM.csv: component list (U1 detailed with its pinout)
- final_integrated.png: visual render of the routing

Board dimensions: 53.335 x 32.75 mm, no mounting holes.
