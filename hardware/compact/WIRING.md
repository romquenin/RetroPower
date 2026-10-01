========================================================================
   RetroPower -- Wiring summary (J1, J2, J3, J4, J6)
========================================================================
Board: RetroPower_Compact (compact version, 40.45 x 32.75mm)
Connectors: male/female headers, 2.54mm pitch (flying wires)


------------------------------------------------------------------------
  HOW TO IDENTIFY PIN 1 ON EACH CONNECTOR
------------------------------------------------------------------------
On every connector on this board, pin 1 can be identified TWO ways,
both visible to the naked eye on the PCB:

  1. Pin 1's COPPER PAD is SQUARE (a solid "square"). Every other pin on
     the same connector has a ROUND pad. This is the most reliable
     marker -- it stays visible even after soldering.

  2. The silkscreen outline (the white/yellow drawing around the
     connector) has a SMALL CORNER CUT OFF (chamfer) on pin 1's side.
     This is the classic marker used on most PCBs.

This is exactly what you spotted on J6 and J4: the square = pin 1, the
small cut corner on the outline = the same marker, pin 1 side.


------------------------------------------------------------------------
  J1 -- To the ESP32 module (flying wires), 5 pins
------------------------------------------------------------------------
  Pin 1 (square): 3V3          -> 3.3V power to the ESP32
  Pin 2          : GND          -> common ground
  Pin 3          : SENSE_MID    -> ESP32's GPIO0 (reads POWER_SENSE)
  Pin 4          : SET_CTRL     -> ESP32's GPIO3 (relay SET command)
  Pin 5          : RESET_CTRL   -> ESP32's GPIO10 (relay RESET command)

  Board orientation: vertical connector, pins running from top (pin 1)
  to bottom (pin 5), on the left edge of the board, next to relay K1.


------------------------------------------------------------------------
  J2 -- Buck converter output (regulated 3.3V), 2 pins
------------------------------------------------------------------------
  Pin 1 (square): 3V3   -> buck's 3.3V output, to the PCB
  Pin 2          : GND   -> common ground

  Board orientation: horizontally-laid connector, under capacitor C1
  (bottom of the board). Pin 1 on the left, pin 2 on the right.


------------------------------------------------------------------------
  J3 -- Raw power tap (to the buck's input), 2 pins
------------------------------------------------------------------------
  Pin 1 (square): RAW_IN -> raw 12V tapped from the console, TO the
                            buck's input (protected by diode D3)
  Pin 2          : GND    -> common ground

  Board orientation: horizontally-laid connector, at the top of the
  board, above J1. Pin 1 on the left, pin 2 on the right.


------------------------------------------------------------------------
  J4 -- Console's original switch (relay pole 1), 3 pins
------------------------------------------------------------------------
  Pin 1 (square): SW_COM  -> original switch's common point
  Pin 2          : SW_NC   -> normally-closed contact (NC)
  Pin 3          : SW_NO   -> normally-open contact (NO)

  Board orientation: vertical connector, on the right edge of the board.
  Pin 1 at the top, pin 3 at the bottom.

  Reminder (confirmed from the Hongfa datasheet): relay K1 pole 1 =
  COM pin 4, NC pin 6, NO pin 8.


------------------------------------------------------------------------
  J6 -- Console POWER_SENSE tap (already at 3.3V), 2 pins
------------------------------------------------------------------------
  Pin 1 (square): SENSE_MID -> same signal as GPIO0/J1.3 (connected
                               directly to the console's internal 3.3V
                               rail, with NO voltage divider -- already
                               validated on your SNES)
  Pin 2          : GND       -> common ground

  Board orientation: vertical connector, on the right edge of the board,
  below J4. Pin 1 at the top, pin 2 at the bottom.


------------------------------------------------------------------------
  QUICK SUMMARY (overview)
------------------------------------------------------------------------
  J1 (5 pins): 3V3 - GND - SENSE_MID - SET_CTRL - RESET_CTRL
  J2 (2 pins): 3V3 - GND
  J3 (2 pins): RAW_IN - GND
  J4 (3 pins): SW_COM - SW_NC - SW_NO
  J6 (2 pins): SENSE_MID - GND

  Note: J1.3 and J6.1 carry the SAME electrical signal (SENSE_MID) --
  that's normal, they're two different access points to the same wire.

  (J5, not needed here, is relay pole 2 -- free/reserved, same pins as
  J4 but on SW2_COM/SW2_NC/SW2_NO.)
========================================================================
