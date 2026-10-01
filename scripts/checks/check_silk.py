#!/usr/bin/env python3
"""Verificateur de recouvrement de serigraphie (mime 'silk_overlap' /
'silk_over_copper' de KiCad, de facon approximative) : verifie que le
champ reference (F.Silkscreen) de chaque empreinte ne chevauche ni les
segments de serigraphie des AUTRES empreintes, ni les pastilles (masque
de soudure) des autres empreintes."""
import pcbnew
from shapely.geometry import box

import sys
board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb")

def to_mm(nm):
    return nm / 1e6

def bbox_of(item):
    bb = item.GetBoundingBox()
    return box(to_mm(bb.GetLeft()), to_mm(bb.GetTop()), to_mm(bb.GetRight()), to_mm(bb.GetBottom()))

ref_boxes = {}   # ref -> shapely box (reference text on F.Silkscreen)
silk_segs = {}   # ref -> list of shapely boxes (silkscreen graphic items)
pad_boxes = {}   # ref -> list of shapely boxes (pads, copper/mask)

for fp in board.GetFootprints():
    ref = fp.GetReference()
    rf = fp.Reference()
    if board.GetLayerName(rf.GetLayer()) == "F.Silkscreen" and rf.IsVisible():
        ref_boxes[ref] = bbox_of(rf)
    segs = []
    for item in fp.GraphicalItems():
        if board.GetLayerName(item.GetLayer()) == "F.Silkscreen":
            segs.append(bbox_of(item))
    silk_segs[ref] = segs
    pads = []
    for p in fp.Pads():
        pads.append(bbox_of(p))
    pad_boxes[ref] = pads

violations = []
for ref_a, tbox in ref_boxes.items():
    for ref_b, segs in silk_segs.items():
        if ref_a == ref_b:
            continue
        for sb in segs:
            if tbox.intersects(sb):
                violations.append((ref_b, ref_a, "silk_overlap"))
    for ref_b, pads in pad_boxes.items():
        # NB : contrairement au recouvrement de serigraphie (segment vs
        # texte), silk_over_copper s'applique aussi au PROPRE composant :
        # le DRC officiel a bien signale le champ reference de K1 puis de
        # C1 chevauchant une pastille DE LEUR PROPRE empreinte -- donc pas
        # d'exclusion "meme composant" ici.
        for pb in pads:
            if tbox.intersects(pb):
                violations.append((ref_b, ref_a, "silk_over_copper"))

print(f"Champs reference verifies: {len(ref_boxes)}")
print(f"Recouvrements detectes: {len(violations)}")
for a, b, kind in violations:
    print(f"  [{kind}] element de {a} <-> champ reference de {b}")
if not violations:
    print("OK : aucun recouvrement de serigraphie detecte.")
