#!/usr/bin/env python3
"""
RetroPower USB Switch -- builds the unrouted board (placement + nets).

Wi-Fi switch that sends a 2.5" USB disk (Y cable: A = data + 5 V,
B = 5 V only) to console 1 (A1/B1) or console 2 (A2/B2).

  K1 (HFD2/003-M-L2-D)  : D- and D+   (pole 1 = D-, pole 2 = D+)
  K2 (HFD2/003-M-L2-D)  : 5V_A and 5V_B
  COM = disk side, NC (relay RESET) = console 1, NO (relay SET) = console 2.
  Both SET coils driven by Q1, both RESET coils by Q2, coils on +5V.
  GND common to every port.

Relay pinout reused from RetroPower (validated on hardware):
  1, 2 = coil +   16 = SET coil -   15 = RESET coil -
  4 COM1, 6 NC1, 8 NO1  |  13 COM2, 11 NC2, 9 NO2

D1 mini (WEMOS_D1_mini_light pads):
  9 = 5V, 10 = G, 14 = D1 (GPIO5, SET), 13 = D2 (GPIO4, RESET)

Coordinates in mm, origin top-left, Y down.
"""
import os
import pcbnew

MM = pcbnew.FromMM
KLIB = "/usr/share/kicad/footprints"
HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, "usbswitch.pretty")
OUT = os.path.join(HERE, "RetroPower_USB_Switch_unrouted.kicad_pcb")

W, H = 67.8, 53.2
PITCH = 16.8
PORT_X = [8.7, 8.7 + PITCH, 8.7 + 2 * PITCH, 8.7 + 3 * PITCH]

board = pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)

NETS = ["+5V", "GND", "CTL_SET", "CTL_RST", "G_SET", "G_RST", "SET_DRV", "RST_DRV",
        "DSK_DM", "DSK_DP", "DSK_VA", "DSK_VB",
        "C1_DM", "C1_DP", "C1_VA", "C1_VB",
        "C2_DM", "C2_DP", "C2_VA", "C2_VB"]
nets = {}
for n in NETS:
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni


def load(lib, name, ref, value):
    fp = pcbnew.FootprintLoad(lib, name)
    if fp is None:
        raise RuntimeError(name)
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)
    return fp


def place(fp, x, y, rot=0, back=False):
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    if rot:
        fp.SetOrientationDegrees(rot)


def wire(fp, padnum, net):
    hit = False
    for p in fp.Pads():
        if p.GetNumber() == str(padnum):
            p.SetNet(nets[net])
            hit = True
    if not hit:
        raise RuntimeError(f"{fp.GetReference()} pad {padnum}")


# ---------------------------------------------------------------- USB ports
# rot 180 = opening toward the top edge; rot 0 = opening toward the bottom edge
TOP_CY = 11.55            # front face on y = 0
BOT_CY = H - 11.55        # front face on y = H
ports = [
    # ref, label, x, y, rot, vbus, dm, dp
    ("J3", "A1", PORT_X[0], TOP_CY, 180, "C1_VA", "C1_DM", "C1_DP"),
    ("J4", "B1", PORT_X[1], TOP_CY, 180, "C1_VB", None, None),
    ("J5", "A2", PORT_X[2], TOP_CY, 180, "C2_VA", "C2_DM", "C2_DP"),
    ("J6", "B2", PORT_X[3], TOP_CY, 180, "C2_VB", None, None),
    ("J1", "A", PORT_X[0], BOT_CY, 0, "DSK_VA", "DSK_DM", "DSK_DP"),
    ("J2", "B", PORT_X[1], BOT_CY, 0, "DSK_VB", None, None),
]
J = {}
for ref, label, x, y, rot, vb, dm, dp in ports:
    fp = load(LOCAL, "USB_A_US-306_Horizontal", ref, "USB-A US-306 (" + label + ")")
    place(fp, x, y, rot)
    wire(fp, 1, vb)
    if dm:
        wire(fp, 2, dm)
        wire(fp, 3, dp)
    wire(fp, 4, "GND")
    wire(fp, 5, "GND")
    J[label] = fp

# ---------------------------------------------------------------- relays
RELAY_Y = 16.3
K1 = load(KLIB + "/Package_DIP.pretty", "DIP-16_W7.62mm", "K1", "HFD2/003-M-L2-D (data)")
place(K1, 4.4, RELAY_Y)
K2 = load(KLIB + "/Package_DIP.pretty", "DIP-16_W7.62mm", "K2", "HFD2/003-M-L2-D (5V)")
place(K2, 16.4, RELAY_Y)
# the HFD2 only has 10 pins on the DIP-16 grid: drop the 6 phantom pads
for K in (K1, K2):
    for pd in list(K.Pads()):
        if pd.GetNumber() in ("3", "5", "7", "10", "12", "14"):
            K.Remove(pd)
for K in (K1, K2):
    wire(K, 1, "+5V")
    wire(K, 2, "+5V")
    wire(K, 16, "SET_DRV")
    wire(K, 15, "RST_DRV")
wire(K1, 4, "DSK_DM"); wire(K1, 6, "C1_DM"); wire(K1, 8, "C2_DM")
wire(K1, 13, "DSK_DP"); wire(K1, 11, "C1_DP"); wire(K1, 9, "C2_DP")
wire(K2, 4, "DSK_VA"); wire(K2, 6, "C1_VA"); wire(K2, 8, "C2_VA")
wire(K2, 13, "DSK_VB"); wire(K2, 11, "C1_VB"); wire(K2, 9, "C2_VB")

# ---------------------------------------------------------------- D1 mini
# module board edge: x -1.37..24.23, y -8.21 (antenna) .. 25.99 (micro-USB)
D1_LEFT = W - 0.3 - 25.6
U1X = D1_LEFT + 1.37
U1Y = H - 25.99
U1 = load(KLIB + "/Module.pretty", "WEMOS_D1_mini_light", "U1", "WEMOS D1 mini")
place(U1, U1X, U1Y)
wire(U1, 9, "+5V")
wire(U1, 10, "GND")
wire(U1, 14, "CTL_SET")
wire(U1, 13, "CTL_RST")
ANT_TOP = U1Y - 8.21          # module edge, antenna end
ANT_BOT = U1Y - 1.40          # end of the antenna area

# ---------------------------------------------------------------- SMD under the D1 mini
cx0 = U1X + 2.6               # first usable column under the module
def smd(lib, name, ref, val, x, y, rot=0):
    fp = load(KLIB + "/" + lib, name, ref, val)
    place(fp, x, y, rot)
    return fp

r1y = U1Y + 2.2
D1 = smd("Diode_SMD.pretty", "D_SOD-123", "D1", "1N4148WS", cx0 + 2.5, r1y)
D2 = smd("Diode_SMD.pretty", "D_SOD-123", "D2", "1N4148WS", cx0 + 9.5, r1y)
r2y = U1Y + 5.6
Q1 = smd("Package_TO_SOT_SMD.pretty", "SOT-23", "Q1", "AO3400A", cx0 + 2.2, r2y, 90)
R3 = smd("Resistor_SMD.pretty", "R_0805_2012Metric", "R3", "10k", cx0 + 8.0, r2y)
R1 = smd("Resistor_SMD.pretty", "R_0805_2012Metric", "R1", "100R", cx0 + 14.0, r2y)
r3y = U1Y + 9.6
Q2 = smd("Package_TO_SOT_SMD.pretty", "SOT-23", "Q2", "AO3400A", cx0 + 2.2, r3y, 90)
R4 = smd("Resistor_SMD.pretty", "R_0805_2012Metric", "R4", "10k", cx0 + 8.0, r3y)
R2 = smd("Resistor_SMD.pretty", "R_0805_2012Metric", "R2", "100R", cx0 + 14.0, r3y)
r4y = U1Y + 13.2
D3 = smd("Diode_SMD.pretty", "D_SOD-123", "D3", "1N4148WS", cx0 + 2.5, r4y)
D4 = smd("Diode_SMD.pretty", "D_SOD-123", "D4", "1N4148WS", cx0 + 9.5, r4y)
C2 = smd("Capacitor_SMD.pretty", "C_0805_2012Metric", "C2", "100nF", cx0 + 15.0, U1Y + 16.0)

# KiCad diode footprints: pad 1 = cathode (silkscreen bar), pad 2 = anode.
# Cathode on +5V, anode on the coil's driven end -> the silkscreen is RIGHT.
for D in (D1, D2):
    wire(D, 1, "+5V"); wire(D, 2, "SET_DRV")
for D in (D3, D4):
    wire(D, 1, "+5V"); wire(D, 2, "RST_DRV")
# AO3400A SOT-23: 1 gate, 2 source, 3 drain
wire(Q1, 1, "G_SET"); wire(Q1, 2, "GND"); wire(Q1, 3, "SET_DRV")
wire(Q2, 1, "G_RST"); wire(Q2, 2, "GND"); wire(Q2, 3, "RST_DRV")
wire(R1, 1, "CTL_SET"); wire(R1, 2, "G_SET")
wire(R2, 1, "CTL_RST"); wire(R2, 2, "G_RST")
wire(R3, 1, "G_SET"); wire(R3, 2, "GND")
wire(R4, 1, "G_RST"); wire(R4, 2, "GND")
wire(C2, 1, "+5V"); wire(C2, 2, "GND")

# C1 100 uF -- too tall to sit under the module
C1 = load(KLIB + "/Capacitor_SMD.pretty", "CP_Elec_6.3x5.4", "C1", "100uF/16V")
place(C1, 29.6, 26.5, 90)
wire(C1, 1, "+5V"); wire(C1, 2, "GND")

# ---------------------------------------------------------------- mounting holes (M2.5)
for i, (x, y) in enumerate([(37.0, 18.0), (37.0, 35.0)]):
    mh = load(KLIB + "/MountingHole.pretty", "MountingHole_2.7mm_M2.5", f"H{i+1}", "M2.5")
    place(mh, x, y)

# ---------------------------------------------------------------- outline
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    s.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1))
    board.Add(s)

seg(0, 0, W, 0); seg(W, 0, W, H); seg(W, H, 0, H); seg(0, H, 0, 0)

# ---------------------------------------------------------------- antenna keep-out
def keepout(x1, y1, x2, y2, name):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        ol.Append(MM(x), MM(y))
    board.Add(z)

KEEP_TOP = 16.6
keepout(D1_LEFT - 0.3, KEEP_TOP, W, ANT_BOT, "ANTENNA")

print(f"board {W} x {H} mm")
print(f"D1 mini origin ({U1X:.2f}, {U1Y:.2f}); antenna {ANT_TOP:.2f}..{ANT_BOT:.2f}; keepout from y={KEEP_TOP}")
pcbnew.SaveBoard(OUT, board)
print("saved", OUT)
