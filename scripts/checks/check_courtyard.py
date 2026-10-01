#!/usr/bin/env python3
"""Verifie les collisions PHYSIQUES entre corps de composants (calque
F.Courtyard), en plus de check_clearance_v3b.py qui ne verifie que
pastilles/pistes (electrique). Deux empreintes en double-empreinte (meme
reference logique, ex C1/C1' ou D1/D1') sur les MEMES nets ont le droit de
se chevaucher (une seule sera soudee) -- on ignore ces paires-la.
"""
import sys
from shapely.geometry import box
import pcbnew

BOARD_FILE = sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb"
MARGIN = 0.3  # marge mecanique souhaitee entre corps de composants differents

# paires a ignorer (double-empreinte optionnelle du meme composant logique)
IGNORE_PAIRS = {
    frozenset(("C1", "C1'")),
    frozenset(("D1", "D1'")),
    frozenset(("D2", "D2'")),
    frozenset(("D3", "D3'")),
}

def to_mm(nm):
    return nm / 1e6

board = pcbnew.LoadBoard(BOARD_FILE)

bodies = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    xs = []
    ys = []
    for item in fp.GraphicalItems():
        if board.GetLayerName(item.GetLayer()) == "F.Courtyard":
            bb = item.GetBoundingBox()
            xs += [to_mm(bb.GetLeft()), to_mm(bb.GetRight())]
            ys += [to_mm(bb.GetTop()), to_mm(bb.GetBottom())]
    if xs:
        bodies[ref] = box(min(xs), min(ys), max(xs), max(ys))

refs = list(bodies.keys())
violations = []
for i in range(len(refs)):
    for j in range(i + 1, len(refs)):
        r1, r2 = refs[i], refs[j]
        if frozenset((r1, r2)) in IGNORE_PAIRS:
            continue
        d = bodies[r1].distance(bodies[r2])
        if d < MARGIN:
            violations.append((r1, r2, d))

print(f"Corps (courtyard) verifies: {len(refs)}")
print(f"Collisions (< {MARGIN}mm) entre corps de composants differents: {len(violations)}")
for v in sorted(violations, key=lambda x: x[2]):
    print(f"  {v[0]} <-> {v[1]} : {v[2]:.3f} mm")
if not violations:
    print("OK : aucune collision physique de corps de composant detectee.")
