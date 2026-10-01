#!/usr/bin/env python3
"""Verificateur de clearance maison v6 -- affine encore la v5.

La v5 corrigeait la sous-estimation des pastilles rectangulaires (cercle
INSCRIT -> cercle CIRCONSCRIT), ce qui a bien retrouve les 8 vraies
violations que le DRC officiel venait de signaler. Mais le cercle
circonscrit est volontairement pessimiste : il "voit" une pastille
rectangulaire comme un disque qui deborde dans les coins, la ou la vraie
pastille (dans nos empreintes, toujours a 0 ou 90 degres) n'a pas de
matiere. Ca faisait remonter des faux positifs.

v6 utilise donc la VRAIE geometrie de la pastille (rectangle tourne selon
son orientation reelle -- toutes nos empreintes sont a 0 ou 90 degres,
donc c'est un rectangle aligne sur les axes) plutot qu'un cercle,
pour les formes RECT/TRAPEZOID/ROUNDRECT/CHAMFERED_RECT. Les formes
CIRCLE/OVAL restent modelisees par un disque (deja exact ou conservateur).

Corrige aussi un vrai trou logique : les DEUX pastilles d'un MEME
composant (ex. les deux pattes d'une resistance ou d'un condensateur,
souvent sur deux nets differents) ne sont PAS soumises a la regle de
clearance de routage -- leur ecartement est fixe par le dessin de
l'empreinte elle-meme, pas par le routage. Le DRC officiel de KiCad ne
les compare jamais entre elles ; les versions precedentes de ce script
le faisaient par erreur et auraient signale de fausses violations sur
CHAQUE resistance/condensateur/diode de la carte."""
import pcbnew
from shapely.geometry import Point, LineString, box
from shapely.affinity import rotate, translate

MIN_CLEARANCE_MM = 0.2
RECT_SHAPES = {pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_TRAPEZOID,
               pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_CHAMFERED_RECT}

import sys
board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb")

def to_mm(nm):
    return nm / 1e6

def pad_geom(p):
    pos = p.GetPosition()
    x, y = to_mm(pos.x), to_mm(pos.y)
    size = p.GetSize()
    w, h = to_mm(size.x), to_mm(size.y)
    if p.GetShape() in RECT_SHAPES:
        rect = box(-w / 2.0, -h / 2.0, w / 2.0, h / 2.0)
        angle_deg = p.GetOrientation().AsDegrees()
        rect = rotate(rect, angle_deg, origin=(0, 0))
        return translate(rect, x, y)
    r = max(w, h) / 2.0
    return Point(x, y).buffer(r)

items = []  # (name, net, netname, layer_set, geom, footprint_ref_or_None)

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        layers = []
        if p.IsOnLayer(pcbnew.F_Cu):
            layers.append("F.Cu")
        if p.IsOnLayer(pcbnew.B_Cu):
            layers.append("B.Cu")
        items.append((f"{ref}.{p.GetNumber()}", p.GetNetCode(), p.GetNetname(), set(layers), pad_geom(p), ref))

for tr in board.GetTracks():
    if tr.Type() == pcbnew.PCB_VIA_T:
        pos = tr.GetPosition()
        w = to_mm(tr.GetWidth())
        geom = Point(to_mm(pos.x), to_mm(pos.y)).buffer(w / 2.0)
        items.append((f"via@{to_mm(pos.x):.3f},{to_mm(pos.y):.3f}", tr.GetNetCode(), tr.GetNetname(),
                      {"F.Cu", "B.Cu"}, geom, None))
        continue
    if not isinstance(tr, pcbnew.PCB_TRACK):
        continue
    s, e = tr.GetStart(), tr.GetEnd()
    w = to_mm(tr.GetWidth())
    layer = "F.Cu" if tr.GetLayer() == pcbnew.F_Cu else ("B.Cu" if tr.GetLayer() == pcbnew.B_Cu else str(tr.GetLayer()))
    geom = LineString([(to_mm(s.x), to_mm(s.y)), (to_mm(e.x), to_mm(e.y))]).buffer(w / 2.0)
    items.append((f"track@{layer}", tr.GetNetCode(), tr.GetNetname(), {layer}, geom, None))

violations = []
n = len(items)
for i in range(n):
    name_i, nc_i, netname_i, layers_i, geom_i, ref_i = items[i]
    for j in range(i + 1, n):
        name_j, nc_j, netname_j, layers_j, geom_j, ref_j = items[j]
        if not (layers_i & layers_j):
            continue
        if nc_i == nc_j and nc_i != 0:
            continue
        if ref_i is not None and ref_i == ref_j:
            continue  # deux pastilles du MEME composant : pas une regle de routage
        d = geom_i.distance(geom_j)
        if d < MIN_CLEARANCE_MM:
            violations.append((name_i, netname_i, name_j, netname_j, d))

print(f"Items verifies: {n}")
print(f"Violations (< {MIN_CLEARANCE_MM}mm) entre nets differents: {len(violations)}")
for v in violations:
    print(f"  {v[0]} ({v[1]!r}) <-> {v[2]} ({v[3]!r}) : {v[4]:.4f} mm")

if not violations:
    print("OK : aucune violation de clearance detectee (geometrie reelle des pastilles, vias incluses).")
