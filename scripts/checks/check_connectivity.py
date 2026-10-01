#!/usr/bin/env python3
"""Verificateur de connectivite maison (mime 'unconnected_items' /
'track_dangling' de KiCad) -- le point faible de check_clearance_v3b.py :
une piste peut geometriquement passer pile a l'endroit d'une pastille tout
en etant sur la MAUVAISE couche de cuivre (donc pas reellement connectee).
Ce script construit, pour chaque net, un graphe de vrais contacts
cuivre-cuivre (piste-piste, piste-via, piste-pastille, via-pastille), tous
sur la meme couche (une via relie ses deux couches entre elles), et
verifie que : (1) toutes les pastilles d'un net appartiennent a la meme
composante connexe -- sinon = circuit ouvert ; (2) aucune extremite de
piste n'est "dans le vide" (dangling) -- ne touche ni une autre piste/via,
ni une pastille, a cet endroit ET sur cette couche."""
import pcbnew

TOL = 0.02  # mm -- deux points a moins de cette distance = le meme contact

import sys
board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb")

def to_mm(nm):
    return nm / 1e6

class DSU:
    def __init__(self):
        self.parent = {}
    def find(self, a):
        self.parent.setdefault(a, a)
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

nets = {}  # nc -> {"pads": [...], "tracks": [...], "vias": [...]}

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        nc = p.GetNetCode()
        if nc == 0:
            continue
        pos = p.GetPosition()
        layers = []
        if p.IsOnLayer(pcbnew.F_Cu):
            layers.append(0)
        if p.IsOnLayer(pcbnew.B_Cu):
            layers.append(1)
        nets.setdefault(nc, {"pads": [], "tracks": [], "vias": []})
        nets[nc]["pads"].append((f"{ref}.{p.GetNumber()}", to_mm(pos.x), to_mm(pos.y), layers))

for tr in board.GetTracks():
    nc = tr.GetNetCode()
    if nc == 0:
        continue
    nets.setdefault(nc, {"pads": [], "tracks": [], "vias": []})
    if tr.Type() == pcbnew.PCB_VIA_T:
        pos = tr.GetPosition()
        nets[nc]["vias"].append((to_mm(pos.x), to_mm(pos.y)))
    else:
        s, e = tr.GetStart(), tr.GetEnd()
        layer = 0 if tr.GetLayer() == pcbnew.F_Cu else 1
        nets[nc]["tracks"].append((to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y), layer))

open_circuits = []
dangling = []

for nc, data in nets.items():
    netname = board.FindNet(nc).GetNetname()

    # chaque noeud = (index, x, y, layer, kind, label)
    points = []  # list of [x, y, layer, kind, label]

    pad_layer_idx = []  # groups of indices belonging to the same physical pad
    for name, x, y, layers in data["pads"]:
        group = []
        for l in layers:
            points.append([x, y, l, "pad", name])
            group.append(len(points) - 1)
        pad_layer_idx.append(group)

    via_idx_pairs = []
    for x, y in data["vias"]:
        i_f = len(points); points.append([x, y, 0, "via", "via"])
        i_b = len(points); points.append([x, y, 1, "via", "via"])
        via_idx_pairs.append((i_f, i_b))

    track_end_idx = []  # (idx1, idx2) per track, to union together
    for x1, y1, x2, y2, l in data["tracks"]:
        i1 = len(points); points.append([x1, y1, l, "trk", "trk-end"])
        i2 = len(points); points.append([x2, y2, l, "trk", "trk-end"])
        track_end_idx.append((i1, i2))

    dsu = DSU()
    for i in range(len(points)):
        dsu.parent.setdefault(i, i)

    # union same-track endpoints
    for i1, i2 in track_end_idx:
        dsu.union(i1, i2)
    # union via's two layers at the same position
    for i_f, i_b in via_idx_pairs:
        dsu.union(i_f, i_b)
    # union a THT pad's own F.Cu/B.Cu entries (the plated hole bridges them)
    for group in pad_layer_idx:
        for k in range(1, len(group)):
            dsu.union(group[0], group[k])
    # union any two points within TOL, same layer (real copper contact)
    n = len(points)
    for i in range(n):
        xi, yi, li = points[i][0], points[i][1], points[i][2]
        for j in range(i + 1, n):
            xj, yj, lj = points[j][0], points[j][1], points[j][2]
            if li != lj:
                continue
            if (xi - xj) ** 2 + (yi - yj) ** 2 <= TOL * TOL:
                dsu.union(i, j)

    # dangling check: a track endpoint must touch something ELSE at that
    # exact spot/layer (another track end, a via, or a pad of this net)
    for i1, i2 in track_end_idx:
        for i in (i1, i2):
            xi, yi, li = points[i][0], points[i][1], points[i][2]
            touches_other = False
            for j in range(n):
                if j == i:
                    continue
                xj, yj, lj = points[j][0], points[j][1], points[j][2]
                if lj != li:
                    continue
                if (xi - xj) ** 2 + (yi - yj) ** 2 <= TOL * TOL:
                    touches_other = True
                    break
            if not touches_other:
                dangling.append((netname, xi, yi, "F.Cu" if li == 0 else "B.Cu"))

    pad_indices = [i for i in range(n) if points[i][3] == "pad"]
    pad_names = [(points[i][4], i) for i in pad_indices]
    if len(pad_indices) >= 2:
        roots = set(dsu.find(i) for i in pad_indices)
        if len(roots) > 1:
            open_circuits.append((netname, pad_names))

print(f"Nets verifies: {len(nets)}")
print(f"Circuits ouverts (pastilles du meme net non reliees): {len(open_circuits)}")
for netname, pad_keys in open_circuits:
    names = ", ".join(n for n, _ in pad_keys)
    print(f"  {netname}: {names}")

print(f"Extremites de piste dans le vide (dangling): {len(dangling)}")
for netname, x, y, layer in dangling:
    print(f"  [{netname}] @({x:.4f}, {y:.4f}) sur {layer}")

if not open_circuits and not dangling:
    print("OK : connectivite complete, aucune extremite dans le vide.")
