#!/usr/bin/env python3
"""
Routes the USB switch board: DSN export -> FreeRouting -> SES import,
then GND pours on both layers, zone fill, DRC report.

Track widths (set as DSN classes, FreeRouting honours them):
  5 V lines of the USB ports, +5V, GND : 0.8 mm (up to ~1 A at disk spin-up)
  relay coil drive                       : 0.5 mm
  USB D+/D-                              : 0.3 mm
  logic                                  : 0.25 mm
"""
import re, subprocess, sys, os
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
# working dir for DSN/SES; put freerouting2.jar (FreeRouting 2.0.1) here
SCR = os.environ.get("USBSW_BUILD", os.path.join(HERE, "build"))
os.makedirs(SCR, exist_ok=True)
IN = f"{HERE}/RetroPower_USB_Switch_unrouted.kicad_pcb"
OUT = f"{HERE}/RetroPower_USB_Switch.kicad_pcb"
DSN = f"{SCR}/usbswitch.dsn"
SES = f"{SCR}/usbswitch.ses"
MM = pcbnew.FromMM

POWER = ["+5V", "GND", "DSK_VA", "DSK_VB", "C1_VA", "C1_VB", "C2_VA", "C2_VB"]
COIL = ["SET_DRV", "RST_DRV"]
USB = ["DSK_DM", "DSK_DP", "C1_DM", "C1_DP", "C2_DM", "C2_DP"]
CLEAR = 0.2

board = pcbnew.LoadBoard(IN)
ds = board.GetDesignSettings()
ds.m_TrackMinWidth = MM(0.2)
ds.m_MinClearance = MM(0.2)
ds.m_CopperEdgeClearance = MM(0.3)
ds.m_ViasMinSize = MM(0.6)
ds.m_MinThroughDrill = MM(0.3)
nc = ds.m_NetSettings.m_DefaultNetClass
nc.SetClearance(MM(CLEAR)); nc.SetTrackWidth(MM(0.25))
nc.SetViaDiameter(MM(0.7)); nc.SetViaDrill(MM(0.35))

assert pcbnew.ExportSpecctraDSN(board, DSN), "DSN export failed"
dsn = open(DSN).read()


def q(n):
    return f'"{n}"' if re.search(r'[^A-Za-z0-9_]', n) else n


# remove our nets from the default class, then add one class per width
m = re.search(r'\(class kicad_default(.*?)\(circuit', dsn, re.S)
body = m.group(1)
for n in POWER + COIL + USB:
    body = re.sub(r'(?<=\s)' + re.escape(q(n)) + r'(?=[\s)])', '', body)
dsn = dsn[:m.start(1)] + body + dsn[m.end(1):]
classes = ""
for name, nets, w in (("power", POWER, 0.8), ("coil", COIL, 0.5), ("usb", USB, 0.3)):
    classes += (f'    (class {name} {" ".join(q(n) for n in nets)}\n'
                f'      (circuit (use_via "Via[0-1]_700:350_um"))\n'
                f'      (rule (width {w*1000:.0f}) (clearance {CLEAR*1000:.0f}))\n    )\n')
dsn = re.sub(r'(\s*\)\s*\(wiring)', '\n' + classes + r'\1', dsn, count=1)
open(DSN, "w").write(dsn)

r = subprocess.run(["java", "-Djava.awt.headless=true", "-jar", f"{SCR}/freerouting2.jar", "--gui.enabled=false", "-de", DSN, "-do", SES,
                    "-mp", "40", "-dct", "0"], capture_output=True, text=True, timeout=900)
print(r.stdout[-1500:]); print(r.stderr[-1500:])
assert os.path.exists(SES), "no SES produced"

# ---- SES import (pcbnew.ImportSpecctraSES only works inside the GUI)
def ses_import(board, path):
    txt = open(path).read()
    m = re.search(r'\(routes\s*\(resolution um (\d+)\)', txt)
    div = float(m.group(1)) * 1000.0          # SES units per mm
    routes = txt[m.end():]
    ntracks = nvias = 0
    for nm in re.finditer(r'\(net ("[^"]*"|\S+)(.*?)(?=\(net |\Z)', routes, re.S):
        name = nm.group(1).strip('"')
        net = board.FindNet(name)
        body = nm.group(2)
        for w in re.finditer(r'\(path (\S+) (\d+)((?:\s+-?\d+)+)\s*\)', body):
            layer = pcbnew.F_Cu if w.group(1) == "F.Cu" else pcbnew.B_Cu
            width = int(w.group(2)) / div
            c = [int(v) for v in w.group(3).split()]
            pts = [(c[i] / div, -c[i + 1] / div) for i in range(0, len(c), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
                t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
                t.SetWidth(MM(width)); t.SetLayer(layer); t.SetNet(net)
                board.Add(t); ntracks += 1
        for v in re.finditer(r'\(via "?([^"\s]*)"? (-?\d+) (-?\d+)', body):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(MM(int(v.group(2)) / div), MM(-int(v.group(3)) / div)))
            via.SetWidth(MM(0.7)); via.SetDrill(MM(0.35))
            via.SetNet(net); board.Add(via); nvias += 1
    return ntracks, nvias

print("imported tracks/vias:", ses_import(board, SES))
board.BuildConnectivity()
print("unrouted connections:", board.GetConnectivity().GetUnconnectedCount(True))

# ---- GND pours, both layers
W = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetWidth())
H = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetHeight())
gnd = board.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((0, 0), (W, 0), (W, H), (0, H)):
        ol.Append(MM(x), MM(y))
    board.Add(z)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print("saved", OUT)
