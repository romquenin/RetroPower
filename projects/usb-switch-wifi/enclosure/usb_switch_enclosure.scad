// RetroPower USB Switch -- 3D-printable enclosure (generated, see make_enclosure.py)
// PCB 67.8 x 53.2 mm, 1.6 mm thick. All PCB coordinates are KiCad's (Y down),
// converted here with y_scad = PCB_H - y_kicad.
$fn = 48;
PART = "both";            // "base", "lid" or "both"

PCB_W = 67.8; PCB_H = 53.2; PCB_T = 1.6;
CLR   = 0.25;             // gap between PCB edge and wall
WALL  = 1.6;
FLOOR = 2.0;
STANDOFF = 4.0;           // under the PCB: USB / relay / header pins stick out ~2-3 mm
PCB_Z = FLOOR + STANDOFF; // bottom of the PCB
TOP_Z = PCB_Z + PCB_T;    // top of the PCB
INNER_H = 13.0;           // PCB top -> lid underside (relays measured: count 12 mm)
LID_T = 2.4;              // thick enough for 1 mm deep engraving (JLC SLA: >= 0.8 mm everywhere)
LIP_H = 1.5; LIP_T = 1.5; LIP_CLR = 0.2;

OX = WALL + CLR; OY = WALL + CLR;          // PCB origin inside the box
OUT_W = PCB_W + 2*OX; OUT_H = PCB_H + 2*OY;
BASE_H = TOP_Z + INNER_H;

// USB-A US-306: face 13.3 x 7.1 mm. Opening a bit larger so most plug
// overmoulds can come close to the connector face.
USBA_W = 15.2; USBA_H = 8.4; USBA_ZC = TOP_Z + 7.1/2;
// D1 mini micro-USB: module PCB sits ~2.5 mm above ours (header spacer)
MUSB_W = 15.0; MUSB_H = 9.0; MUSB_ZC = TOP_Z + 2.5 + 1.0 + 1.4;

TOP_PORTS = [[8.70, "A1"], [25.50, "B1"], [42.30, "A2"], [59.10, "B2"]];
BOT_PORTS = [[8.70, "A"], [25.50, "B"]];
HOLES = [[37.00, 18.00], [37.00, 35.00]];
MUSB_X = 54.70;
// support posts under the PCB: under each USB port's front (no pins there)
// and under the D1 mini's micro-USB end
POSTS = [[8.70, 4.0], [25.50, 4.0], [42.30, 4.0], [59.10, 4.0],
         [8.70, 49.20], [25.50, 49.20],
         [54.70, 50.20]];

function sx(x) = OX + x;
function sy(y) = OY + (PCB_H - y);

M25_CLEAR = 2.9; M25_HEAD_D = 5.0; SCREW_L = 20;   // M2.5 x 20 mm + nut: screw tip ends flush with the bottom
SEAT_Z = SCREW_L - BASE_H;          // screw-head seat, in lid coordinates (lid underside = 0)
ENGR = 1.0;                         // engraving depth on the lid
EMB = 0.8;                          // raised labels on the walls
FONT = "DejaVu Sans:style=Bold";
FONT_C = "DejaVu Sans Condensed:style=Bold";   // size 4 -> 0.87 mm stroke, CONSOLE 1 = 30.5 mm wide
NUT_AF = 5.3; NUT_H = 2.2;          // M2.5 nut is 5.0 across flats, +0.3 clearance

module base() {
  difference() {
    union() {
      difference() {
        cube([OUT_W, OUT_H, BASE_H]);
        translate([WALL, WALL, FLOOR]) cube([OUT_W - 2*WALL, OUT_H - 2*WALL, BASE_H]);
      }
      for (h = HOLES) translate([sx(h[0]), sy(h[1]), 0]) cylinder(d = 8, h = PCB_Z);   // wide enough to wrap the nut pocket
      for (p = POSTS) translate([sx(p[0]), sy(p[1]), 0]) cylinder(d = 3, h = PCB_Z);
    }
    // screw + nut trap from below
    for (h = HOLES) translate([sx(h[0]), sy(h[1]), -1]) {
      cylinder(d = M25_CLEAR, h = 50);
      cylinder(d = NUT_AF / cos(30), h = NUT_H + 1, $fn = 6);
    }
    // USB-A openings, back wall (consoles) and front wall (disk)
    for (p = TOP_PORTS) translate([sx(p[0]) - USBA_W/2, OUT_H - WALL - 1, USBA_ZC - USBA_H/2])
      cube([USBA_W, WALL + 2, USBA_H]);
    for (p = BOT_PORTS) translate([sx(p[0]) - USBA_W/2, -1, USBA_ZC - USBA_H/2])
      cube([USBA_W, WALL + 2, USBA_H]);
    // D1 mini micro-USB, front wall
    translate([sx(MUSB_X) - MUSB_W/2, -1, MUSB_ZC - MUSB_H/2]) cube([MUSB_W, WALL + 2, MUSB_H]);
  }
  // raised port names under each opening (0.8 mm, readable from outside)
  LBL_Z = (USBA_ZC - USBA_H/2) / 2 + 0.3;
  for (p = TOP_PORTS) translate([sx(p[0]), OUT_H, LBL_Z]) rotate([90, 0, 180])
    linear_extrude(EMB) text(p[1], size = 4.5, halign = "center", valign = "center", font = FONT);
  for (p = BOT_PORTS) translate([sx(p[0]), 0, LBL_Z]) rotate([90, 0, 0])
    linear_extrude(EMB) text(p[1], size = 4.5, halign = "center", valign = "center", font = FONT);
  translate([sx(MUSB_X), 0, LBL_Z]) rotate([90, 0, 0])
    linear_extrude(EMB) text("5V", size = 4.5, halign = "center", valign = "center", font = FONT);
}

module lid() {
  difference() {
    union() {
      cube([OUT_W, OUT_H, LID_T]);
      // lip that drops inside the walls
      translate([WALL + LIP_CLR, WALL + LIP_CLR, -LIP_H]) difference() {
        cube([OUT_W - 2*(WALL + LIP_CLR), OUT_H - 2*(WALL + LIP_CLR), LIP_H]);
        translate([LIP_T, LIP_T, -1])
          cube([OUT_W - 2*(WALL + LIP_CLR + LIP_T), OUT_H - 2*(WALL + LIP_CLR + LIP_T), LIP_H + 2]);
      }
      // pillars that hold the PCB down
      for (h = HOLES) translate([sx(h[0]), sy(h[1]), -INNER_H]) cylinder(d = 5.5, h = INNER_H);
      // wider collar where the screw head sits (above the USB bodies, 14.7 mm)
      for (h = HOLES) translate([sx(h[0]), sy(h[1]), -4.5]) cylinder(d = 8, h = 4.5);
    }
    for (h = HOLES) translate([sx(h[0]), sy(h[1]), -INNER_H - 1]) cylinder(d = M25_CLEAR, h = 50);
    for (h = HOLES) translate([sx(h[0]), sy(h[1]), SEAT_Z]) cylinder(d = M25_HEAD_D + 0.4, h = 10);
    // engraved labels, 1 mm deep, strokes >= 0.8 mm
    translate([(sx(TOP_PORTS[0][0]) + sx(TOP_PORTS[1][0]))/2, OUT_H - 6, LID_T - ENGR])
      linear_extrude(ENGR + 1) text("CONSOLE 1", size = 4, halign = "center", valign = "center", font = FONT_C);
    translate([(sx(TOP_PORTS[2][0]) + sx(TOP_PORTS[3][0]))/2, OUT_H - 6, LID_T - ENGR])
      linear_extrude(ENGR + 1) text("CONSOLE 2", size = 4, halign = "center", valign = "center", font = FONT_C);
    translate([(sx(BOT_PORTS[0][0]) + sx(BOT_PORTS[1][0]))/2, 6, LID_T - ENGR])
      linear_extrude(ENGR + 1) text("DISQUE", size = 4, halign = "center", valign = "center", font = FONT_C);
  }
}

if (PART == "base") base();
if (PART == "lid")  translate([0, OUT_H, LID_T]) rotate([180, 0, 0]) lid();   // printed upside down
if (PART == "both") { base(); translate([0, 0, BASE_H]) lid(); }
