#!/usr/bin/env python3
"""Verificateur hole-to-hole maison (mime la regle DRC 'hole_to_hole' de
KiCad) -- verifie TOUS les couples de trous perces (pastilles traversantes
+ vias, tous nets confondus y compris le meme net) et flague tout couple
plus proche que le minimum mecanique de percage.

KiCad exige par defaut ~0.2495mm (mesure sur le rapport DRC fourni par
l'utilisateur) ; on verifie ici avec ce meme seuil (marge de securite
retiree pour reproduire fidelement ce que KiCad flaguerait)."""
import pcbnew

MIN_HOLE_TO_HOLE_MM = 0.2495

import sys
board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb")

def to_mm(nm):
    return nm / 1e6

holes = []  # (name, x_mm, y_mm, hole_radius_mm)

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        drill = p.GetDrillSize()
        if drill.x > 0:
            pos = p.GetPosition()
            holes.append((f"pad {ref}.{p.GetNumber()}", to_mm(pos.x), to_mm(pos.y), to_mm(drill.x) / 2.0))

for tr in board.GetTracks():
    if tr.Type() == pcbnew.PCB_VIA_T:
        pos = tr.GetPosition()
        holes.append((f"via[{tr.GetNetname()}]", to_mm(pos.x), to_mm(pos.y), to_mm(tr.GetDrill()) / 2.0))

violations = []
n = len(holes)
for i in range(n):
    ni, xi, yi, ri = holes[i]
    for j in range(i + 1, n):
        nj, xj, yj, rj = holes[j]
        d = ((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5
        gap = d - ri - rj
        if gap < MIN_HOLE_TO_HOLE_MM:
            violations.append((ni, (xi, yi), nj, (xj, yj), gap))

print(f"Trous verifies: {n}")
print(f"Violations hole-to-hole (< {MIN_HOLE_TO_HOLE_MM}mm de marge): {len(violations)}")
for v in violations:
    print(f"  {v[0]} @{v[1]} <-> {v[2]} @{v[3]} : marge {v[4]:.4f} mm")

if not violations:
    print("OK : aucune violation hole-to-hole detectee.")
